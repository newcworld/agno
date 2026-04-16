from dataclasses import dataclass
from datetime import datetime
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field

from agno.models.base import Model
from agno.models.utils import get_model
from agno.run.agent import Message
from agno.utils.log import log_debug, log_warning

if TYPE_CHECKING:
    pass


@dataclass
class RunProgressSummary:
    """Progress snapshot for a running agent, persisted with periodic saves."""

    summary: str
    artifacts: Optional[List[str]] = None
    next_steps: Optional[str] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        _dict: Dict[str, Any] = {
            "summary": self.summary,
            "artifacts": self.artifacts,
            "next_steps": self.next_steps,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        return {k: v for k, v in _dict.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RunProgressSummary":
        updated_at = data.get("updated_at")
        if updated_at and isinstance(updated_at, str):
            data = {**data, "updated_at": datetime.fromisoformat(updated_at)}
        return cls(**data)


class RunProgressSummaryResponse(BaseModel):
    summary: str = Field(
        ...,
        description="Concise summary of work completed so far, focusing on key accomplishments and deliverables.",
    )
    artifacts: Optional[List[str]] = Field(
        None,
        description="File paths, URLs, or identifiers of artifacts produced (e.g. docs/prd.md, deployed URL).",
    )
    next_steps: Optional[str] = Field(
        None,
        description="What was being worked on or about to start when this snapshot was taken.",
    )


@dataclass
class RunProgressSummaryManager:
    """Generates periodic progress summaries during long-running agent executions."""

    model: Optional[Model] = None
    interval: float = 30.0
    last_message_count: int = 0

    def get_response_format(self, model: "Model") -> Union[Dict[str, Any], Type[BaseModel]]:
        if model.supports_native_structured_outputs:
            return RunProgressSummaryResponse
        elif model.supports_json_schema_outputs:
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": RunProgressSummaryResponse.__name__,
                    "schema": RunProgressSummaryResponse.model_json_schema(),
                },
            }
        else:
            return {"type": "json_object"}

    def _build_messages(
        self,
        messages: List[Message],
        previous_summary: Optional[Dict[str, Any]],
        response_format: Union[Dict[str, Any], Type[BaseModel]],
    ) -> List[Message]:
        system_prompt = dedent("""\
        You are a progress tracker for an AI agent that is executing a long-running task.
        Analyze the conversation below and produce a concise progress snapshot.

        Focus on:
        - What work has been completed (summary)
        - What artifacts have been produced: file paths, URLs, deployment targets, etc. (artifacts)
        - What is currently being worked on or about to start (next_steps)

        Be factual and concise. Only include information present in the conversation.
        """)

        if previous_summary:
            system_prompt += (
                f"\n<previous_progress_summary>\n{previous_summary.get('summary', '')}\n</previous_progress_summary>\n"
            )
            system_prompt += "Update the summary with any new progress since the previous snapshot.\n"

        conversation_lines: list[str] = []
        recent_messages = messages[-40:] if len(messages) > 40 else messages
        for msg in recent_messages:
            if msg.role == "system":
                continue
            content = msg.content if isinstance(msg.content, str) else str(msg.content) if msg.content else ""
            if not content.strip():
                continue
            truncated = content[:500] + "..." if len(content) > 500 else content
            role_label = msg.role.capitalize()
            conversation_lines.append(f"{role_label}: {truncated}")

        if not conversation_lines:
            return []

        system_prompt += "\n<conversation>\n"
        system_prompt += "\n".join(conversation_lines)
        system_prompt += "\n</conversation>"

        if response_format == {"type": "json_object"}:
            from agno.utils.prompts import get_json_output_prompt

            system_prompt += "\n" + get_json_output_prompt(RunProgressSummaryResponse)

        return [
            Message(role="system", content=system_prompt),
            Message(role="user", content="Provide the progress summary."),
        ]

    def _process_response(self, response: Any, model: "Model") -> Optional[RunProgressSummary]:
        from datetime import datetime

        if response is None:
            return None

        if (
            model.supports_native_structured_outputs
            and response.parsed is not None
            and isinstance(response.parsed, RunProgressSummaryResponse)
        ):
            return RunProgressSummary(
                summary=response.parsed.summary,
                artifacts=response.parsed.artifacts,
                next_steps=response.parsed.next_steps,
                updated_at=datetime.now(),
            )

        if isinstance(response.content, str):
            try:
                from agno.utils.string import parse_response_model_str

                parsed: Optional[RunProgressSummaryResponse] = parse_response_model_str(
                    response.content, RunProgressSummaryResponse
                )
                if parsed is not None:
                    return RunProgressSummary(
                        summary=parsed.summary,
                        artifacts=parsed.artifacts,
                        next_steps=parsed.next_steps,
                        updated_at=datetime.now(),
                    )
            except Exception as e:
                log_warning(f"Failed to parse progress summary response: {e}")

        return None

    def should_update(self, message_count: int) -> bool:
        """Check if there are new messages worth summarizing since the last update."""
        if message_count <= self.last_message_count:
            return False
        return True

    async def acreate_progress_summary(
        self,
        messages: List[Message],
        previous_summary: Optional[Dict[str, Any]] = None,
    ) -> Optional[RunProgressSummary]:
        log_debug("Creating run progress summary", center=True)
        self.model = get_model(self.model)
        if self.model is None:
            return None

        if not self.should_update(len(messages)):
            return None
        self.last_message_count = len(messages)

        response_format = self.get_response_format(self.model)
        summary_messages = self._build_messages(messages, previous_summary, response_format)
        if not summary_messages:
            return None

        try:
            response = await self.model.aresponse(messages=summary_messages, response_format=response_format)
        except Exception as e:
            log_warning(f"Failed to generate progress summary: {e}")
            return None

        result = self._process_response(response, self.model)
        if result:
            log_debug("Run progress summary created", center=True)
        return result

    def create_progress_summary(
        self,
        messages: List[Message],
        previous_summary: Optional[Dict[str, Any]] = None,
    ) -> Optional[RunProgressSummary]:
        log_debug("Creating run progress summary", center=True)
        self.model = get_model(self.model)
        if self.model is None:
            return None

        if not self.should_update(len(messages)):
            return None
        self.last_message_count = len(messages)

        response_format = self.get_response_format(self.model)
        summary_messages = self._build_messages(messages, previous_summary, response_format)
        if not summary_messages:
            return None

        try:
            response = self.model.response(messages=summary_messages, response_format=response_format)
        except Exception as e:
            log_warning(f"Failed to generate progress summary: {e}")
            return None

        result = self._process_response(response, self.model)
        if result:
            log_debug("Run progress summary created", center=True)
        return result
