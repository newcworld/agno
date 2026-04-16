"""AgentOS scheduler configuration (lock renewal interval)."""

from agno.agent.agent import Agent
from agno.os import AgentOS


def test_scheduler_lock_renew_interval_default() -> None:
    agent = Agent()
    os = AgentOS(agents=[agent], telemetry=False, scheduler=False)
    assert os._scheduler_lock_renew_interval == 120


def test_scheduler_lock_renew_interval_custom() -> None:
    agent = Agent()
    os = AgentOS(
        agents=[agent],
        telemetry=False,
        scheduler=False,
        scheduler_lock_renew_interval=60,
    )
    assert os._scheduler_lock_renew_interval == 60
