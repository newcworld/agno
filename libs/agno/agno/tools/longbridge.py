import json
import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

from agno.tools import Toolkit
from agno.utils.log import log_debug

try:
    from longbridge.openapi import (
        AdjustType,
        CalcIndex,
        Config,
        ContentContext,
        Market,
        OpenApiException,
        OrderSide,
        OrderStatus,
        OrderType,
        OutsideRTH,
        Period,
        QuoteContext,
        SecuritiesUpdateMode,
        SortOrderType,
        TimeInForceType,
        TradeContext,
        WarrantSortBy,
    )
except ImportError:
    raise ImportError("`longbridge` not installed. Please install using `pip install longbridge`.")

# ── Literal type aliases ────────────────────────────────────────

PeriodType = Literal[
    "1m",
    "2m",
    "3m",
    "5m",
    "10m",
    "15m",
    "20m",
    "30m",
    "45m",
    "60m",
    "1h",
    "2h",
    "3h",
    "4h",
    "1d",
    "day",
    "1w",
    "week",
    "1M",
    "month",
    "quarter",
    "year",
]
MarketType = Literal["HK", "US", "CN", "SG"]
AdjustTypeStr = Literal["none", "forward"]
OrderSideStr = Literal["Buy", "Sell"]
OrderTypeStr = Literal[
    "LO",
    "ELO",
    "MO",
    "AO",
    "ALO",
    "ODD",
    "LIT",
    "MIT",
    "TSLPAMT",
    "TSLPPCT",
    "TSMAMT",
    "TSMPCT",
    "SLO",
]
TimeInForceStr = Literal["Day", "GoodTilCanceled", "GoodTilDate"]
OutsideRTHStr = Literal["RTHOnly", "AnyTime", "Overnight"]
OrderStatusStr = Literal[
    "NotReported",
    "New",
    "WaitToNew",
    "PartialFilled",
    "Filled",
    "WaitToReplace",
    "PendingReplace",
    "Replaced",
    "WaitToCancel",
    "PendingCancel",
    "Rejected",
    "Canceled",
    "Expired",
    "PartialWithdrawal",
]
WarrantSortByStr = Literal["LastDone", "ChangeRate", "Volume", "Price", "Premium", "Leverage"]
SortOrderStr = Literal["Ascending", "Descending"]
UpdateModeStr = Literal["Add", "Remove", "Replace"]

# ── Enum mapping constants ──────────────────────────────────────

PERIOD_MAP: Dict[str, Period] = {
    "1m": Period.Min_1,
    "2m": Period.Min_2,
    "3m": Period.Min_3,
    "5m": Period.Min_5,
    "10m": Period.Min_10,
    "15m": Period.Min_15,
    "20m": Period.Min_20,
    "30m": Period.Min_30,
    "45m": Period.Min_45,
    "60m": Period.Min_60,
    "1h": Period.Min_60,
    "2h": Period.Min_120,
    "3h": Period.Min_180,
    "4h": Period.Min_240,
    "1d": Period.Day,
    "day": Period.Day,
    "1w": Period.Week,
    "week": Period.Week,
    "1M": Period.Month,
    "month": Period.Month,
    "quarter": Period.Quarter,
    "year": Period.Year,
}

MARKET_MAP: Dict[str, Market] = {
    "HK": Market.HK,
    "US": Market.US,
    "CN": Market.CN,
    "SG": Market.SG,
}

ADJUST_MAP: Dict[str, AdjustType] = {
    "none": AdjustType.NoAdjust,
    "forward": AdjustType.ForwardAdjust,
}

ORDER_SIDE_MAP: Dict[str, OrderSide] = {
    "Buy": OrderSide.Buy,
    "Sell": OrderSide.Sell,
}

ORDER_TYPE_MAP: Dict[str, OrderType] = {
    "LO": OrderType.LO,
    "ELO": OrderType.ELO,
    "MO": OrderType.MO,
    "AO": OrderType.AO,
    "ALO": OrderType.ALO,
    "ODD": OrderType.ODD,
    "LIT": OrderType.LIT,
    "MIT": OrderType.MIT,
    "TSLPAMT": OrderType.TSLPAMT,
    "TSLPPCT": OrderType.TSLPPCT,
    "TSMAMT": OrderType.TSMAMT,
    "TSMPCT": OrderType.TSMPCT,
    "SLO": OrderType.SLO,
}

TIME_IN_FORCE_MAP: Dict[str, TimeInForceType] = {
    "Day": TimeInForceType.Day,
    "GoodTilCanceled": TimeInForceType.GoodTilCanceled,
    "GoodTilDate": TimeInForceType.GoodTilDate,
}

OUTSIDE_RTH_MAP: Dict[str, OutsideRTH] = {
    "RTHOnly": OutsideRTH.RTHOnly,
    "AnyTime": OutsideRTH.AnyTime,
    "Overnight": OutsideRTH.Overnight,
}

ORDER_STATUS_MAP: Dict[str, OrderStatus] = {
    "NotReported": OrderStatus.NotReported,
    "New": OrderStatus.New,
    "WaitToNew": OrderStatus.WaitToNew,
    "PartialFilled": OrderStatus.PartialFilled,
    "Filled": OrderStatus.Filled,
    "WaitToReplace": OrderStatus.WaitToReplace,
    "PendingReplace": OrderStatus.PendingReplace,
    "Replaced": OrderStatus.Replaced,
    "WaitToCancel": OrderStatus.WaitToCancel,
    "PendingCancel": OrderStatus.PendingCancel,
    "Rejected": OrderStatus.Rejected,
    "Canceled": OrderStatus.Canceled,
    "Expired": OrderStatus.Expired,
    "PartialWithdrawal": OrderStatus.PartialWithdrawal,
}

WARRANT_SORT_BY_MAP: Dict[str, WarrantSortBy] = {
    "LastDone": WarrantSortBy.LastDone,
    "ChangeRate": WarrantSortBy.ChangeRate,
    "Volume": WarrantSortBy.Volume,
    "Price": WarrantSortBy.Price,
    "Premium": WarrantSortBy.Premium,
    "Leverage": WarrantSortBy.Leverage,
}

SORT_ORDER_MAP: Dict[str, SortOrderType] = {
    "Ascending": SortOrderType.Ascending,
    "Descending": SortOrderType.Descending,
}

UPDATE_MODE_MAP: Dict[str, SecuritiesUpdateMode] = {
    "Add": SecuritiesUpdateMode.Add,
    "Remove": SecuritiesUpdateMode.Remove,
    "Replace": SecuritiesUpdateMode.Replace,
}

CALC_INDEX_MAP: Dict[str, CalcIndex] = {
    "LastDone": CalcIndex.LastDone,
    "ChangeValue": CalcIndex.ChangeValue,
    "ChangeRate": CalcIndex.ChangeRate,
    "Volume": CalcIndex.Volume,
    "Turnover": CalcIndex.Turnover,
    "Amplitude": CalcIndex.Amplitude,
    "VolumeRatio": CalcIndex.VolumeRatio,
    "TurnoverRate": CalcIndex.TurnoverRate,
    "TotalMarketValue": CalcIndex.TotalMarketValue,
    "CapitalFlow": CalcIndex.CapitalFlow,
    "YtdChangeRate": CalcIndex.YtdChangeRate,
    "FiveDayChangeRate": CalcIndex.FiveDayChangeRate,
    "TenDayChangeRate": CalcIndex.TenDayChangeRate,
    "HalfYearChangeRate": CalcIndex.HalfYearChangeRate,
    "FiveMinutesChangeRate": CalcIndex.FiveMinutesChangeRate,
    "PeTtmRatio": CalcIndex.PeTtmRatio,
    "PbRatio": CalcIndex.PbRatio,
    "DividendRatioTtm": CalcIndex.DividendRatioTtm,
    "ExpiryDate": CalcIndex.ExpiryDate,
    "StrikePrice": CalcIndex.StrikePrice,
    "ImpliedVolatility": CalcIndex.ImpliedVolatility,
    "Delta": CalcIndex.Delta,
    "Gamma": CalcIndex.Gamma,
    "Theta": CalcIndex.Theta,
    "Vega": CalcIndex.Vega,
    "Rho": CalcIndex.Rho,
}


# ── Helpers ─────────────────────────────────────────────────────


def _serialize(obj: Any) -> Any:
    """Recursively convert SDK objects to JSON-safe dicts."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, list):
        return [_serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if hasattr(obj, "__dict__"):
        return {k: _serialize(v) for k, v in vars(obj).items() if not k.startswith("_")}
    return str(obj)


def _to_json(obj: Any) -> str:
    """Serialize SDK response to JSON string."""
    return json.dumps(_serialize(obj), indent=2, ensure_ascii=False, default=str)


class LongbridgeTools(Toolkit):
    """
    LongbridgeTools provides access to Longbridge OpenAPI for market data, trading, and content.

    Covers HK, US, CN (SH/SZ), SG markets. Uses traditional API Key authentication.

    Args:
        app_key: Longbridge App Key. Defaults to LONGBRIDGE_APP_KEY env var.
        app_secret: Longbridge App Secret. Defaults to LONGBRIDGE_APP_SECRET env var.
        access_token: Longbridge Access Token. Defaults to LONGBRIDGE_ACCESS_TOKEN env var.
        enable_quote: Enable quote tools (quote, static_info, depth, brokers, trades, intraday, participants, filings).
        enable_candlesticks: Enable candlestick/historical data tools.
        enable_calc_indexes: Enable financial index calculation tool.
        enable_options: Enable options tools (chain expiry, chain info, option quote).
        enable_warrants: Enable warrants tools (issuers, list, quote).
        enable_market_info: Enable market info tools (trading calendar, capital flow, market temperature, security list).
        enable_watchlist: Enable watchlist management tools.
        enable_trade: Enable trading tools (orders, positions, account balance, margin).
        enable_content: Enable content tools (news, topics).
        all: Enable all tools. Overrides individual flags when True.
    """

    def __init__(
        self,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        enable_quote: bool = True,
        enable_candlesticks: bool = True,
        enable_calc_indexes: bool = False,
        enable_options: bool = False,
        enable_warrants: bool = False,
        enable_market_info: bool = False,
        enable_watchlist: bool = False,
        enable_trade: bool = False,
        enable_content: bool = False,
        all: bool = False,
        **kwargs,
    ):
        self._app_key = app_key or os.getenv("LONGBRIDGE_APP_KEY")
        self._app_secret = app_secret or os.getenv("LONGBRIDGE_APP_SECRET")
        self._access_token = access_token or os.getenv("LONGBRIDGE_ACCESS_TOKEN")

        self._config: Optional[Config] = None
        self._quote_ctx: Optional[QuoteContext] = None
        self._trade_ctx: Optional[TradeContext] = None
        self._content_ctx: Optional[ContentContext] = None

        tools: List[Any] = []

        # Quote tools
        if all or enable_quote:
            tools.extend(
                [
                    self.get_quote,
                    self.get_static_info,
                    self.get_depth,
                    self.get_brokers,
                    self.get_trades,
                    self.get_intraday,
                    self.get_participants,
                    self.get_filings,
                ]
            )

        # Candlestick tools
        if all or enable_candlesticks:
            tools.extend(
                [
                    self.get_candlesticks,
                    self.get_history_candlesticks,
                ]
            )

        # Calc indexes
        if all or enable_calc_indexes:
            tools.append(self.get_calc_indexes)

        # Options tools
        if all or enable_options:
            tools.extend(
                [
                    self.get_option_chain_expiry_dates,
                    self.get_option_chain_info,
                    self.get_option_quote,
                ]
            )

        # Warrants tools
        if all or enable_warrants:
            tools.extend(
                [
                    self.get_warrant_issuers,
                    self.get_warrant_list,
                    self.get_warrant_quote,
                ]
            )

        # Market info tools
        if all or enable_market_info:
            tools.extend(
                [
                    self.get_trading_session,
                    self.get_trading_days,
                    self.get_capital_flow,
                    self.get_capital_distribution,
                    self.get_market_temperature,
                    self.get_security_list,
                ]
            )

        # Watchlist tools
        if all or enable_watchlist:
            tools.extend(
                [
                    self.get_watchlist,
                    self.create_watchlist_group,
                    self.update_watchlist_group,
                    self.delete_watchlist_group,
                ]
            )

        # Trade tools
        if all or enable_trade:
            tools.extend(
                [
                    self.submit_order,
                    self.replace_order,
                    self.cancel_order,
                    self.get_today_orders,
                    self.get_history_orders,
                    self.get_order_detail,
                    self.get_today_executions,
                    self.get_history_executions,
                    self.get_account_balance,
                    self.get_cash_flow,
                    self.get_stock_positions,
                    self.get_fund_positions,
                    self.get_margin_ratio,
                    self.estimate_max_purchase_quantity,
                ]
            )

        # Content tools
        if all or enable_content:
            tools.extend(
                [
                    self.get_news,
                    self.get_topics,
                ]
            )

        super().__init__(name="longbridge_tools", tools=tools, **kwargs)

    @property
    def config(self) -> Config:
        if self._config is None:
            if self._app_key and self._app_secret and self._access_token:
                self._config = Config.from_apikey(self._app_key, self._app_secret, self._access_token)
            else:
                self._config = Config.from_apikey_env()
        return self._config

    @property
    def quote_ctx(self) -> QuoteContext:
        if self._quote_ctx is None:
            self._quote_ctx = QuoteContext(self.config)
        return self._quote_ctx

    @property
    def trade_ctx(self) -> TradeContext:
        if self._trade_ctx is None:
            self._trade_ctx = TradeContext(self.config)
        return self._trade_ctx

    @property
    def content_ctx(self) -> ContentContext:
        if self._content_ctx is None:
            self._content_ctx = ContentContext(self.config)
        return self._content_ctx

    # ── Quote Tools ──────────────────────────────────────────────

    def get_quote(self, symbols: str) -> str:
        """Get real-time quotes for one or more securities.

        Args:
            symbols: Comma-separated symbols, e.g. "700.HK,AAPL.US,TSLA.US"

        Returns:
            str: JSON with quote data including last_done, open, high, low, volume, turnover.
        """
        try:
            symbol_list = [s.strip() for s in symbols.split(",")]
            log_debug(f"Fetching quotes for {symbol_list}")
            resp = self.quote_ctx.quote(symbol_list)
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching quotes: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching quotes: {e}"

    def get_static_info(self, symbols: str) -> str:
        """Get static information for securities (name, exchange, lot_size, EPS, etc.).

        Args:
            symbols: Comma-separated symbols, e.g. "700.HK,AAPL.US"

        Returns:
            str: JSON with security static info.
        """
        try:
            symbol_list = [s.strip() for s in symbols.split(",")]
            log_debug(f"Fetching static info for {symbol_list}")
            resp = self.quote_ctx.static_info(symbol_list)
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching static info: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching static info: {e}"

    def get_depth(self, symbol: str) -> str:
        """Get order book depth (Level 2 bid/ask) for a security.

        Args:
            symbol: Security symbol, e.g. "700.HK"

        Returns:
            str: JSON with asks and bids arrays (position, price, volume, order_num).
        """
        try:
            log_debug(f"Fetching depth for {symbol}")
            resp = self.quote_ctx.depth(symbol)
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching depth: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching depth: {e}"

    def get_brokers(self, symbol: str) -> str:
        """Get broker queue for a security (HK market only).

        Args:
            symbol: HK security symbol, e.g. "700.HK"

        Returns:
            str: JSON with ask_brokers and bid_brokers arrays.
        """
        try:
            log_debug(f"Fetching brokers for {symbol}")
            resp = self.quote_ctx.brokers(symbol)
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching brokers: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching brokers: {e}"

    def get_trades(self, symbol: str, count: int = 50) -> str:
        """Get recent tick-by-tick trades for a security.

        Args:
            symbol: Security symbol, e.g. "700.HK"
            count: Number of trades to retrieve (max 1000). Default: 50.

        Returns:
            str: JSON with trade records.
        """
        try:
            log_debug(f"Fetching trades for {symbol}")
            resp = self.quote_ctx.trades(symbol, count)
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching trades: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching trades: {e}"

    def get_intraday(self, symbol: str) -> str:
        """Get intraday price lines for a security.

        Args:
            symbol: Security symbol, e.g. "700.HK"

        Returns:
            str: JSON with intraday line data.
        """
        try:
            log_debug(f"Fetching intraday data for {symbol}")
            resp = self.quote_ctx.intraday(symbol)
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching intraday: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching intraday: {e}"

    def get_participants(self) -> str:
        """Get participant broker info (HK market only).

        Returns:
            str: JSON with participant info list.
        """
        try:
            log_debug("Fetching participants")
            resp = self.quote_ctx.participants()
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching participants: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching participants: {e}"

    def get_filings(self, symbol: str) -> str:
        """Get regulatory filings for a security (earnings reports, announcements, etc.).

        Args:
            symbol: Security symbol, e.g. "700.HK"

        Returns:
            str: JSON with filing records (title, type, url, published_at).
        """
        try:
            log_debug(f"Fetching filings for {symbol}")
            resp = self.quote_ctx.filings(symbol)
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching filings: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching filings: {e}"

    # ── Candlestick Tools ────────────────────────────────────────

    def get_candlesticks(
        self, symbol: str, period: PeriodType = "day", count: int = 100, adjust: AdjustTypeStr = "none"
    ) -> str:
        """Get recent candlestick (K-line) data for a security.

        Args:
            symbol: Security symbol, e.g. "700.HK"
            period: Candlestick period. Values: 1m,2m,3m,5m,10m,15m,20m,30m,45m,60m/1h,2h,3h,4h,
                    1d/day,1w/week,1M/month,quarter,year. Default: "day".
            count: Number of candlesticks to retrieve. Default: 100.
            adjust: Adjustment type. "none" or "forward". Default: "none".

        Returns:
            str: JSON with candlestick data (open, high, low, close, volume, turnover, timestamp).
        """
        try:
            log_debug(f"Fetching candlesticks for {symbol}")
            resp = self.quote_ctx.candlesticks(symbol, PERIOD_MAP[period], count, ADJUST_MAP[adjust])
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching candlesticks: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching candlesticks: {e}"

    def get_history_candlesticks(
        self, symbol: str, start: str, end: str, period: PeriodType = "day", adjust: AdjustTypeStr = "none"
    ) -> str:
        """Get historical candlestick data for a security within a date range.

        Args:
            symbol: Security symbol, e.g. "700.HK"
            start: Start date in YYYY-MM-DD format.
            end: End date in YYYY-MM-DD format.
            period: Candlestick period. Values: 1m,5m,15m,30m,60m/1h,1d/day,1w/week,1M/month. Default: "day".
            adjust: Adjustment type. "none" or "forward". Default: "none".

        Returns:
            str: JSON with historical candlestick data.
        """
        try:
            log_debug(f"Fetching history candlesticks for {symbol} from {start} to {end}")
            resp = self.quote_ctx.history_candlesticks_by_date(
                symbol,
                PERIOD_MAP[period],
                ADJUST_MAP[adjust],
                start=date.fromisoformat(start),
                end=date.fromisoformat(end),
            )
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching history candlesticks: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching history candlesticks: {e}"

    # ── Calc Indexes Tool ────────────────────────────────────────

    def get_calc_indexes(self, symbols: str, indexes: str) -> str:
        """Calculate financial indexes for securities (PE, PB, market cap, change rate, etc.).

        Args:
            symbols: Comma-separated symbols, e.g. "700.HK,AAPL.US"
            indexes: Comma-separated index names. Available indexes:
                     LastDone, ChangeValue, ChangeRate, Volume, Turnover, Amplitude,
                     VolumeRatio, TurnoverRate, TotalMarketValue, CapitalFlow,
                     YtdChangeRate, FiveDayChangeRate, TenDayChangeRate,
                     HalfYearChangeRate, FiveMinutesChangeRate,
                     PeTtmRatio, PbRatio, DividendRatioTtm,
                     ExpiryDate, StrikePrice, ImpliedVolatility, Delta, Gamma, Theta, Vega, Rho

        Returns:
            str: JSON with calculated index values per security.
        """
        try:
            symbol_list = [s.strip() for s in symbols.split(",")]
            index_names = [s.strip() for s in indexes.split(",")]

            calc_indexes = []
            for name in index_names:
                if name in CALC_INDEX_MAP:
                    calc_indexes.append(CALC_INDEX_MAP[name])
                else:
                    return f"Unknown index '{name}'. Available: {list(CALC_INDEX_MAP.keys())}"

            log_debug(f"Fetching calc indexes for {symbol_list}")
            resp = self.quote_ctx.calc_indexes(symbol_list, calc_indexes)
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching calc indexes: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching calc indexes: {e}"

    # ── Options Tools ────────────────────────────────────────────

    def get_option_chain_expiry_dates(self, symbol: str) -> str:
        """Get option chain expiry dates for an underlying security.

        Args:
            symbol: Underlying symbol, e.g. "AAPL.US"

        Returns:
            str: JSON list of expiry dates.
        """
        try:
            log_debug(f"Fetching option chain expiry dates for {symbol}")
            resp = self.quote_ctx.option_chain_expiry_date_list(symbol)
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching option chain dates: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching option chain dates: {e}"

    def get_option_chain_info(self, symbol: str, expiry_date: str) -> str:
        """Get option chain strike prices for a specific expiry date.

        Args:
            symbol: Underlying symbol, e.g. "AAPL.US"
            expiry_date: Expiry date in YYYY-MM-DD format.

        Returns:
            str: JSON with strike price info (price, call_symbol, put_symbol, standard).
        """
        try:
            log_debug(f"Fetching option chain info for {symbol} on {expiry_date}")
            resp = self.quote_ctx.option_chain_info_by_date(symbol, date.fromisoformat(expiry_date))
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching option chain info: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching option chain info: {e}"

    def get_option_quote(self, symbols: str) -> str:
        """Get real-time quotes for option contracts.

        Args:
            symbols: Comma-separated option symbols, e.g. "AAPL230317P160000.US"

        Returns:
            str: JSON with option quote data.
        """
        try:
            symbol_list = [s.strip() for s in symbols.split(",")]
            log_debug(f"Fetching option quotes for {symbol_list}")
            resp = self.quote_ctx.option_quote(symbol_list)
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching option quotes: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching option quotes: {e}"

    # ── Warrants Tools ───────────────────────────────────────────

    def get_warrant_issuers(self) -> str:
        """Get list of warrant issuers (HK market).

        Returns:
            str: JSON with issuer info list.
        """
        try:
            log_debug("Fetching warrant issuers")
            resp = self.quote_ctx.warrant_issuers()
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching warrant issuers: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching warrant issuers: {e}"

    def get_warrant_list(
        self,
        symbol: str,
        sort_by: WarrantSortByStr = "LastDone",
        sort_order: SortOrderStr = "Ascending",
    ) -> str:
        """Get list of warrants for an underlying security.

        Args:
            symbol: Underlying symbol, e.g. "700.HK"
            sort_by: Sort field. Values: LastDone, ChangeRate, Volume, Price, Premium, Leverage.
            sort_order: Sort order. Values: Ascending, Descending.

        Returns:
            str: JSON with warrant list.
        """
        try:
            log_debug(f"Fetching warrant list for {symbol}")
            resp = self.quote_ctx.warrant_list(
                symbol,
                sort_by=WARRANT_SORT_BY_MAP[sort_by],
                sort_order=SORT_ORDER_MAP[sort_order],
            )
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching warrant list: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching warrant list: {e}"

    def get_warrant_quote(self, symbols: str) -> str:
        """Get real-time quotes for warrants.

        Args:
            symbols: Comma-separated warrant symbols, e.g. "21125.HK"

        Returns:
            str: JSON with warrant quote data.
        """
        try:
            symbol_list = [s.strip() for s in symbols.split(",")]
            log_debug(f"Fetching warrant quotes for {symbol_list}")
            resp = self.quote_ctx.warrant_quote(symbol_list)
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching warrant quotes: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching warrant quotes: {e}"

    # ── Market Info Tools ────────────────────────────────────────

    def get_trading_session(self) -> str:
        """Get trading session times for all markets.

        Returns:
            str: JSON with trading session info per market.
        """
        try:
            log_debug("Fetching trading sessions")
            resp = self.quote_ctx.trading_session()
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching trading sessions: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching trading sessions: {e}"

    def get_trading_days(self, market: MarketType, start: str, end: str) -> str:
        """Get trading days for a market within a date range (max 1 month interval).

        Args:
            market: Market code. Values: HK, US, CN, SG.
            start: Start date in YYYY-MM-DD format.
            end: End date in YYYY-MM-DD format.

        Returns:
            str: JSON with trading_days and half_trading_days lists.
        """
        try:
            log_debug(f"Fetching trading days for {market}")
            resp = self.quote_ctx.trading_days(MARKET_MAP[market], date.fromisoformat(start), date.fromisoformat(end))
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching trading days: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching trading days: {e}"

    def get_capital_flow(self, symbol: str) -> str:
        """Get capital flow data for a security.

        Args:
            symbol: Security symbol, e.g. "700.HK"

        Returns:
            str: JSON with capital flow line data.
        """
        try:
            log_debug(f"Fetching capital flow for {symbol}")
            resp = self.quote_ctx.capital_flow(symbol)
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching capital flow: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching capital flow: {e}"

    def get_capital_distribution(self, symbol: str) -> str:
        """Get capital distribution for a security (small/medium/large/extra-large orders).

        Args:
            symbol: Security symbol, e.g. "700.HK"

        Returns:
            str: JSON with capital distribution breakdown.
        """
        try:
            log_debug(f"Fetching capital distribution for {symbol}")
            resp = self.quote_ctx.capital_distribution(symbol)
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching capital distribution: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching capital distribution: {e}"

    def get_market_temperature(self, market: MarketType) -> str:
        """Get market sentiment temperature index (0-100) for a market.

        Args:
            market: Market code. Values: HK, US, CN, SG.

        Returns:
            str: JSON with market temperature value.
        """
        try:
            log_debug(f"Fetching market temperature for {market}")
            resp = self.quote_ctx.market_temperature(MARKET_MAP[market])
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching market temperature: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching market temperature: {e}"

    def get_security_list(self, market: MarketType) -> str:
        """Get list of all securities in a market.

        Args:
            market: Market code. Values: HK, US, CN, SG.

        Returns:
            str: JSON with securities list.
        """
        try:
            log_debug(f"Fetching security list for {market}")
            resp = self.quote_ctx.security_list(MARKET_MAP[market])
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching security list: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching security list: {e}"

    # ── Watchlist Tools ──────────────────────────────────────────

    def get_watchlist(self) -> str:
        """Get all watchlist groups and their securities.

        Returns:
            str: JSON with watchlist groups.
        """
        try:
            log_debug("Fetching watchlist")
            resp = self.quote_ctx.watchlist()
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching watchlist: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching watchlist: {e}"

    def create_watchlist_group(self, name: str, securities: str = "") -> str:
        """Create a new watchlist group.

        Args:
            name: Group name.
            securities: Comma-separated symbols to add, e.g. "700.HK,AAPL.US". Optional.

        Returns:
            str: Group ID of the created group.
        """
        try:
            sec_list = [s.strip() for s in securities.split(",") if s.strip()] if securities else []
            log_debug(f"Creating watchlist group '{name}'")
            group_id = self.quote_ctx.create_watchlist_group(name, securities=sec_list if sec_list else None)
            return json.dumps({"group_id": group_id})
        except OpenApiException as e:
            return f"Error creating watchlist group: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error creating watchlist group: {e}"

    def update_watchlist_group(
        self, group_id: int, name: str = "", securities: str = "", mode: UpdateModeStr = "Add"
    ) -> str:
        """Update a watchlist group (rename, add/remove/replace securities).

        Args:
            group_id: The watchlist group ID to update.
            name: New group name. Leave empty to keep unchanged.
            securities: Comma-separated symbols, e.g. "700.HK,AAPL.US".
            mode: Update mode for securities. Values: Add, Remove, Replace. Default: Add.

        Returns:
            str: Success or error message.
        """
        try:
            sec_list = [s.strip() for s in securities.split(",") if s.strip()] if securities else []

            log_debug(f"Updating watchlist group {group_id}")
            self.quote_ctx.update_watchlist_group(
                group_id,
                name=name if name else None,
                securities=sec_list if sec_list else None,
                mode=UPDATE_MODE_MAP[mode],
            )
            return json.dumps({"status": "success", "group_id": group_id})
        except OpenApiException as e:
            return f"Error updating watchlist group: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error updating watchlist group: {e}"

    def delete_watchlist_group(self, group_id: int, purge: bool = False) -> str:
        """Delete a watchlist group.

        Args:
            group_id: The watchlist group ID to delete.
            purge: If True, permanently delete; if False, move to trash.

        Returns:
            str: Success or error message.
        """
        try:
            log_debug(f"Deleting watchlist group {group_id}")
            self.quote_ctx.delete_watchlist_group(group_id, purge=purge)
            return json.dumps({"status": "success", "group_id": group_id, "purged": purge})
        except OpenApiException as e:
            return f"Error deleting watchlist group: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error deleting watchlist group: {e}"

    # ── Trade Tools ──────────────────────────────────────────────

    def submit_order(
        self,
        symbol: str,
        side: OrderSideStr,
        order_type: OrderTypeStr,
        quantity: str,
        time_in_force: TimeInForceStr = "Day",
        price: Optional[str] = None,
        trigger_price: Optional[str] = None,
        remark: Optional[str] = None,
        expire_date: Optional[str] = None,
        outside_rth: Optional[OutsideRTHStr] = None,
    ) -> str:
        """Submit a new order.

        Args:
            symbol: Security symbol, e.g. "700.HK"
            side: Order side. Values: Buy, Sell.
            order_type: Order type. Values: LO (Limit), ELO (Enhanced Limit), MO (Market),
                        AO (At-Auction), ALO (At-Auction Limit), ODD (Odd Lots),
                        LIT (Limit If Touched), MIT (Market If Touched).
            quantity: Order quantity as string, e.g. "100".
            time_in_force: Time in force. Values: Day, GoodTilCanceled, GoodTilDate. Default: Day.
            price: Limit price as string. Required for LO, ELO, ALO, ODD, LIT orders.
            trigger_price: Trigger price as string. Required for LIT, MIT orders.
            remark: Optional order remark (max 64 chars).
            expire_date: Expiry date (YYYY-MM-DD) for GoodTilDate time_in_force.
            outside_rth: US market only. Values: RTHOnly, AnyTime, Overnight.

        Returns:
            str: JSON with order_id on success.
        """
        try:
            log_debug(f"Submitting order for {symbol}")
            resp = self.trade_ctx.submit_order(
                symbol=symbol,
                order_type=ORDER_TYPE_MAP[order_type],
                side=ORDER_SIDE_MAP[side],
                submitted_quantity=Decimal(quantity),
                time_in_force=TIME_IN_FORCE_MAP[time_in_force],
                submitted_price=Decimal(price) if price else None,
                trigger_price=Decimal(trigger_price) if trigger_price else None,
                expire_date=date.fromisoformat(expire_date) if expire_date else None,
                outside_rth=OUTSIDE_RTH_MAP[outside_rth] if outside_rth else None,
                remark=remark,
            )
            return json.dumps({"order_id": str(resp.order_id)})
        except OpenApiException as e:
            return f"Error submitting order: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error submitting order: {e}"

    def replace_order(self, order_id: str, quantity: str, price: str) -> str:
        """Replace (modify) an existing order's quantity and/or price.

        Args:
            order_id: The order ID to modify.
            quantity: New quantity as string.
            price: New price as string.

        Returns:
            str: Success or error message.
        """
        try:
            log_debug(f"Replacing order {order_id}")
            self.trade_ctx.replace_order(
                order_id=order_id,
                quantity=Decimal(quantity),
                price=Decimal(price),
            )
            return json.dumps({"status": "success", "order_id": order_id})
        except OpenApiException as e:
            return f"Error replacing order: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error replacing order: {e}"

    def cancel_order(self, order_id: str) -> str:
        """Cancel an existing order.

        Args:
            order_id: The order ID to cancel.

        Returns:
            str: Success or error message.
        """
        try:
            log_debug(f"Canceling order {order_id}")
            self.trade_ctx.cancel_order(order_id)
            return json.dumps({"status": "success", "order_id": order_id})
        except OpenApiException as e:
            return f"Error canceling order: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error canceling order: {e}"

    def get_today_orders(self, symbol: Optional[str] = None, status: Optional[str] = None) -> str:
        """Get today's orders, optionally filtered by symbol and/or status.

        Args:
            symbol: Optional security symbol filter, e.g. "700.HK".
            status: Optional comma-separated status filter.
                    Values: NotReported, New, WaitToNew, PartialFilled, Filled,
                    WaitToReplace, PendingReplace, Replaced, WaitToCancel,
                    PendingCancel, Rejected, Canceled, Expired, PartialWithdrawal.

        Returns:
            str: JSON with today's order list.
        """
        try:
            parsed_status = None
            if status:
                parsed_status = [
                    ORDER_STATUS_MAP[s.strip()] for s in status.split(",") if s.strip() in ORDER_STATUS_MAP
                ]

            log_debug("Fetching today's orders")
            resp = self.trade_ctx.today_orders(
                symbol=symbol,
                status=parsed_status,
            )
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching today's orders: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching today's orders: {e}"

    def get_history_orders(
        self,
        start: str,
        end: str,
        symbol: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        """Get historical orders within a date range.

        Args:
            start: Start date in YYYY-MM-DD format.
            end: End date in YYYY-MM-DD format.
            symbol: Optional security symbol filter.
            status: Optional comma-separated status filter (same values as get_today_orders).

        Returns:
            str: JSON with historical order list.
        """
        try:
            parsed_status = None
            if status:
                parsed_status = [
                    ORDER_STATUS_MAP[s.strip()] for s in status.split(",") if s.strip() in ORDER_STATUS_MAP
                ]

            log_debug("Fetching history orders")
            resp = self.trade_ctx.history_orders(
                symbol=symbol,
                status=parsed_status,
                start_at=datetime.strptime(start, "%Y-%m-%d"),
                end_at=datetime.strptime(end, "%Y-%m-%d"),
            )
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching history orders: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching history orders: {e}"

    def get_order_detail(self, order_id: str) -> str:
        """Get detailed information about a specific order, including charge breakdown.

        Args:
            order_id: The order ID to query.

        Returns:
            str: JSON with order detail.
        """
        try:
            log_debug(f"Fetching order detail for {order_id}")
            resp = self.trade_ctx.order_detail(order_id)
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching order detail: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching order detail: {e}"

    def get_today_executions(self, symbol: Optional[str] = None, order_id: Optional[str] = None) -> str:
        """Get today's execution (fill) records.

        Args:
            symbol: Optional security symbol filter.
            order_id: Optional order ID filter.

        Returns:
            str: JSON with execution records (trade_id, symbol, price, quantity, trade_done_at).
        """
        try:
            log_debug("Fetching today's executions")
            resp = self.trade_ctx.today_executions(
                symbol=symbol,
                order_id=order_id,
            )
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching today's executions: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching today's executions: {e}"

    def get_history_executions(self, start: str, end: str, symbol: Optional[str] = None) -> str:
        """Get historical execution (fill) records within a date range.

        Args:
            start: Start date in YYYY-MM-DD format.
            end: End date in YYYY-MM-DD format.
            symbol: Optional security symbol filter.

        Returns:
            str: JSON with historical execution records.
        """
        try:
            log_debug("Fetching history executions")
            resp = self.trade_ctx.history_executions(
                symbol=symbol,
                start_at=datetime.strptime(start, "%Y-%m-%d"),
                end_at=datetime.strptime(end, "%Y-%m-%d"),
            )
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching history executions: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching history executions: {e}"

    def get_account_balance(self, currency: Optional[str] = None) -> str:
        """Get account balance summary (total cash, buying power, margin, risk level).

        Args:
            currency: Optional currency filter, e.g. "HKD", "USD".

        Returns:
            str: JSON with account balance details per currency.
        """
        try:
            log_debug("Fetching account balance")
            resp = self.trade_ctx.account_balance(currency=currency)
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching account balance: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching account balance: {e}"

    def get_cash_flow(self, start: str, end: str, symbol: Optional[str] = None, page: int = 1, size: int = 50) -> str:
        """Get cash flow records within a date range.

        Args:
            start: Start date in YYYY-MM-DD format.
            end: End date in YYYY-MM-DD format.
            symbol: Optional security symbol filter.
            page: Page number. Default: 1.
            size: Page size. Default: 50.

        Returns:
            str: JSON with cash flow records.
        """
        try:
            log_debug("Fetching cash flow")
            resp = self.trade_ctx.cash_flow(
                start_at=datetime.strptime(start, "%Y-%m-%d"),
                end_at=datetime.strptime(end, "%Y-%m-%d"),
                symbol=symbol,
                page=page,
                size=size,
            )
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching cash flow: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching cash flow: {e}"

    def get_stock_positions(self, symbols: Optional[str] = None) -> str:
        """Get stock positions (holdings).

        Args:
            symbols: Optional comma-separated symbols filter, e.g. "700.HK,AAPL.US".

        Returns:
            str: JSON with stock positions grouped by channel.
        """
        try:
            log_debug("Fetching stock positions")
            symbol_list = [s.strip() for s in symbols.split(",")] if symbols else None
            resp = self.trade_ctx.stock_positions(symbols=symbol_list)
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching stock positions: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching stock positions: {e}"

    def get_fund_positions(self, symbols: Optional[str] = None) -> str:
        """Get fund positions (holdings).

        Args:
            symbols: Optional comma-separated fund symbols filter.

        Returns:
            str: JSON with fund positions.
        """
        try:
            log_debug("Fetching fund positions")
            symbol_list = [s.strip() for s in symbols.split(",")] if symbols else None
            resp = self.trade_ctx.fund_positions(symbols=symbol_list)
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching fund positions: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching fund positions: {e}"

    def get_margin_ratio(self, symbol: str) -> str:
        """Get margin ratio for a security (initial, maintenance, forced liquidation factors).

        Args:
            symbol: Security symbol, e.g. "TSLA.US"

        Returns:
            str: JSON with margin ratio (im_factor, mm_factor, fm_factor).
        """
        try:
            log_debug(f"Fetching margin ratio for {symbol}")
            resp = self.trade_ctx.margin_ratio(symbol)
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching margin ratio: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching margin ratio: {e}"

    def estimate_max_purchase_quantity(
        self,
        symbol: str,
        side: OrderSideStr,
        order_type: OrderTypeStr,
        price: str,
        currency: Optional[str] = None,
    ) -> str:
        """Estimate the maximum purchase quantity for a security.

        Args:
            symbol: Security symbol, e.g. "700.HK"
            side: Order side. Values: Buy, Sell.
            order_type: Order type. Values: LO, MO, etc.
            price: Estimated price as string.
            currency: Optional currency, e.g. "HKD".

        Returns:
            str: JSON with cash_max_qty and margin_max_qty.
        """
        try:
            log_debug(f"Estimating max purchase quantity for {symbol}")
            resp = self.trade_ctx.estimate_max_purchase_quantity(
                symbol=symbol,
                order_type=ORDER_TYPE_MAP[order_type],
                side=ORDER_SIDE_MAP[side],
                price=Decimal(price),
                currency=currency,
            )
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error estimating max quantity: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error estimating max quantity: {e}"

    # ── Content Tools ────────────────────────────────────────────

    def get_news(self, symbol: str) -> str:
        """Get latest news articles for a security.

        Args:
            symbol: Security symbol, e.g. "700.HK"

        Returns:
            str: JSON with news items (id, title, description, url, published_at,
                 likes_count, comments_count, shares_count).
        """
        try:
            log_debug(f"Fetching news for {symbol}")
            resp = self.content_ctx.news(symbol)
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching news: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching news: {e}"

    def get_topics(self, symbol: str) -> str:
        """Get community discussion topics for a security.

        Args:
            symbol: Security symbol, e.g. "700.HK"

        Returns:
            str: JSON with topic items (id, title, description, url, published_at,
                 likes_count, comments_count, shares_count).
        """
        try:
            log_debug(f"Fetching topics for {symbol}")
            resp = self.content_ctx.topics(symbol)
            return _to_json(resp)
        except OpenApiException as e:
            return f"Error fetching topics: code={e.code}, message={e.message}"
        except Exception as e:
            return f"Error fetching topics: {e}"
