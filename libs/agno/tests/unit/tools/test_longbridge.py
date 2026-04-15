"""Unit tests for LongbridgeTools class."""

import json
import sys
from datetime import date, datetime
from decimal import Decimal
from types import ModuleType
from unittest.mock import MagicMock, Mock, patch

import pytest

# ── Mock the longbridge SDK before importing LongbridgeTools ────────────

_mock_lb = ModuleType("longbridge")
_mock_openapi = ModuleType("longbridge.openapi")

# Enum-like sentinels
_mock_openapi.AdjustType = MagicMock()
_mock_openapi.AdjustType.NoAdjust = "NoAdjust"
_mock_openapi.AdjustType.ForwardAdjust = "ForwardAdjust"

_mock_openapi.Config = MagicMock()
_mock_openapi.ContentContext = MagicMock()
_mock_openapi.QuoteContext = MagicMock()
_mock_openapi.TradeContext = MagicMock()

_mock_openapi.Market = MagicMock()
_mock_openapi.Market.HK = "HK"
_mock_openapi.Market.US = "US"
_mock_openapi.Market.CN = "CN"
_mock_openapi.Market.SG = "SG"

_mock_openapi.Period = MagicMock()
_mock_openapi.Period.Min_1 = "Min_1"
_mock_openapi.Period.Min_2 = "Min_2"
_mock_openapi.Period.Min_3 = "Min_3"
_mock_openapi.Period.Min_5 = "Min_5"
_mock_openapi.Period.Min_10 = "Min_10"
_mock_openapi.Period.Min_15 = "Min_15"
_mock_openapi.Period.Min_20 = "Min_20"
_mock_openapi.Period.Min_30 = "Min_30"
_mock_openapi.Period.Min_45 = "Min_45"
_mock_openapi.Period.Min_60 = "Min_60"
_mock_openapi.Period.Min_120 = "Min_120"
_mock_openapi.Period.Min_180 = "Min_180"
_mock_openapi.Period.Min_240 = "Min_240"
_mock_openapi.Period.Day = "Day"
_mock_openapi.Period.Week = "Week"
_mock_openapi.Period.Month = "Month"
_mock_openapi.Period.Quarter = "Quarter"
_mock_openapi.Period.Year = "Year"

_mock_openapi.OrderSide = MagicMock()
_mock_openapi.OrderSide.Buy = "Buy"
_mock_openapi.OrderSide.Sell = "Sell"

_mock_openapi.OrderType = MagicMock()
_mock_openapi.OrderType.LO = "LO"
_mock_openapi.OrderType.ELO = "ELO"
_mock_openapi.OrderType.MO = "MO"
_mock_openapi.OrderType.AO = "AO"
_mock_openapi.OrderType.ALO = "ALO"
_mock_openapi.OrderType.ODD = "ODD"
_mock_openapi.OrderType.LIT = "LIT"
_mock_openapi.OrderType.MIT = "MIT"
_mock_openapi.OrderType.TSLPAMT = "TSLPAMT"
_mock_openapi.OrderType.TSLPPCT = "TSLPPCT"
_mock_openapi.OrderType.TSMAMT = "TSMAMT"
_mock_openapi.OrderType.TSMPCT = "TSMPCT"
_mock_openapi.OrderType.SLO = "SLO"

_mock_openapi.TimeInForceType = MagicMock()
_mock_openapi.TimeInForceType.Day = "Day"
_mock_openapi.TimeInForceType.GoodTilCanceled = "GoodTilCanceled"
_mock_openapi.TimeInForceType.GoodTilDate = "GoodTilDate"

_mock_openapi.OrderStatus = MagicMock()
_mock_openapi.OrderStatus.NotReported = "NotReported"
_mock_openapi.OrderStatus.New = "New"
_mock_openapi.OrderStatus.WaitToNew = "WaitToNew"
_mock_openapi.OrderStatus.PartialFilled = "PartialFilled"
_mock_openapi.OrderStatus.Filled = "Filled"
_mock_openapi.OrderStatus.WaitToReplace = "WaitToReplace"
_mock_openapi.OrderStatus.PendingReplace = "PendingReplace"
_mock_openapi.OrderStatus.Replaced = "Replaced"
_mock_openapi.OrderStatus.WaitToCancel = "WaitToCancel"
_mock_openapi.OrderStatus.PendingCancel = "PendingCancel"
_mock_openapi.OrderStatus.Rejected = "Rejected"
_mock_openapi.OrderStatus.Canceled = "Canceled"
_mock_openapi.OrderStatus.Expired = "Expired"
_mock_openapi.OrderStatus.PartialWithdrawal = "PartialWithdrawal"

_mock_openapi.OutsideRTH = MagicMock()
_mock_openapi.OutsideRTH.RTHOnly = "RTHOnly"
_mock_openapi.OutsideRTH.AnyTime = "AnyTime"
_mock_openapi.OutsideRTH.Overnight = "Overnight"

_mock_openapi.CalcIndex = MagicMock()
_mock_openapi.CalcIndex.LastDone = "LastDone"
_mock_openapi.CalcIndex.PeTtmRatio = "PeTtmRatio"
_mock_openapi.CalcIndex.PbRatio = "PbRatio"
_mock_openapi.CalcIndex.TotalMarketValue = "TotalMarketValue"
_mock_openapi.CalcIndex.ChangeRate = "ChangeRate"
_mock_openapi.CalcIndex.ChangeValue = "ChangeValue"
_mock_openapi.CalcIndex.Volume = "Volume"
_mock_openapi.CalcIndex.Turnover = "Turnover"
_mock_openapi.CalcIndex.Amplitude = "Amplitude"
_mock_openapi.CalcIndex.VolumeRatio = "VolumeRatio"
_mock_openapi.CalcIndex.TurnoverRate = "TurnoverRate"
_mock_openapi.CalcIndex.CapitalFlow = "CapitalFlow"
_mock_openapi.CalcIndex.YtdChangeRate = "YtdChangeRate"
_mock_openapi.CalcIndex.FiveDayChangeRate = "FiveDayChangeRate"
_mock_openapi.CalcIndex.TenDayChangeRate = "TenDayChangeRate"
_mock_openapi.CalcIndex.HalfYearChangeRate = "HalfYearChangeRate"
_mock_openapi.CalcIndex.FiveMinutesChangeRate = "FiveMinutesChangeRate"
_mock_openapi.CalcIndex.DividendRatioTtm = "DividendRatioTtm"
_mock_openapi.CalcIndex.ExpiryDate = "ExpiryDate"
_mock_openapi.CalcIndex.StrikePrice = "StrikePrice"
_mock_openapi.CalcIndex.ImpliedVolatility = "ImpliedVolatility"
_mock_openapi.CalcIndex.Delta = "Delta"
_mock_openapi.CalcIndex.Gamma = "Gamma"
_mock_openapi.CalcIndex.Theta = "Theta"
_mock_openapi.CalcIndex.Vega = "Vega"
_mock_openapi.CalcIndex.Rho = "Rho"

_mock_openapi.SecuritiesUpdateMode = MagicMock()
_mock_openapi.SecuritiesUpdateMode.Add = "Add"
_mock_openapi.SecuritiesUpdateMode.Remove = "Remove"
_mock_openapi.SecuritiesUpdateMode.Replace = "Replace"

_mock_openapi.WarrantSortBy = MagicMock()
_mock_openapi.WarrantSortBy.LastDone = "LastDone"
_mock_openapi.WarrantSortBy.ChangeRate = "ChangeRate"
_mock_openapi.WarrantSortBy.Volume = "Volume"
_mock_openapi.WarrantSortBy.Price = "Price"
_mock_openapi.WarrantSortBy.Premium = "Premium"
_mock_openapi.WarrantSortBy.Leverage = "Leverage"

_mock_openapi.SortOrderType = MagicMock()
_mock_openapi.SortOrderType.Ascending = "Ascending"
_mock_openapi.SortOrderType.Descending = "Descending"

_mock_openapi.SubType = MagicMock()


class MockOpenApiException(Exception):
    def __init__(self, code=0, message="mock error", trace_id="trace-123"):
        self.code = code
        self.message = message
        self.trace_id = trace_id
        super().__init__(message)


_mock_openapi.OpenApiException = MockOpenApiException

_mock_lb.openapi = _mock_openapi
sys.modules["longbridge"] = _mock_lb
sys.modules["longbridge.openapi"] = _mock_openapi

from agno.tools.longbridge import (  # noqa: E402
    ADJUST_MAP,
    CALC_INDEX_MAP,
    MARKET_MAP,
    ORDER_SIDE_MAP,
    ORDER_STATUS_MAP,
    ORDER_TYPE_MAP,
    OUTSIDE_RTH_MAP,
    PERIOD_MAP,
    SORT_ORDER_MAP,
    TIME_IN_FORCE_MAP,
    UPDATE_MODE_MAP,
    WARRANT_SORT_BY_MAP,
    LongbridgeTools,
    _serialize,
    _to_json,
)


# ── Helper Function Tests ───────────────────────────────────────


class TestSerialize:
    def test_none(self):
        assert _serialize(None) is None

    def test_primitives(self):
        assert _serialize("hello") == "hello"
        assert _serialize(42) == 42
        assert _serialize(3.14) == 3.14
        assert _serialize(True) is True

    def test_decimal(self):
        assert _serialize(Decimal("50.00")) == 50.0

    def test_datetime(self):
        dt = datetime(2024, 6, 1, 10, 30, 0)
        assert _serialize(dt) == "2024-06-01T10:30:00"

    def test_date(self):
        d = date(2024, 6, 1)
        assert _serialize(d) == "2024-06-01"

    def test_list(self):
        assert _serialize([1, "a", None]) == [1, "a", None]

    def test_dict(self):
        assert _serialize({"key": Decimal("1.5")}) == {"key": 1.5}

    def test_nested_list(self):
        result = _serialize([{"price": Decimal("100")}, {"price": Decimal("200")}])
        assert result == [{"price": 100.0}, {"price": 200.0}]

    def test_object_with_dict(self):
        obj = Mock()
        obj.__dict__ = {"symbol": "700.HK", "price": Decimal("350"), "_private": "hidden"}
        result = _serialize(obj)
        assert result == {"symbol": "700.HK", "price": 350.0}
        assert "_private" not in result

    def test_unknown_type(self):
        class Custom:
            def __str__(self):
                return "custom_str"

        # Custom class without __dict__ entries worth showing
        result = _serialize(Custom())
        assert isinstance(result, (str, dict))


class TestToJson:
    def test_simple(self):
        result = _to_json({"symbol": "AAPL.US", "price": 150})
        data = json.loads(result)
        assert data["symbol"] == "AAPL.US"
        assert data["price"] == 150

    def test_ensure_ascii_false(self):
        result = _to_json({"name": "腾讯控股"})
        assert "腾讯控股" in result

    def test_list(self):
        result = _to_json([1, 2, 3])
        assert json.loads(result) == [1, 2, 3]


class TestMappingConstants:
    @pytest.mark.parametrize(
        "key,expected",
        [
            ("1m", "Min_1"),
            ("5m", "Min_5"),
            ("15m", "Min_15"),
            ("30m", "Min_30"),
            ("60m", "Min_60"),
            ("1h", "Min_60"),
            ("2h", "Min_120"),
            ("3h", "Min_180"),
            ("4h", "Min_240"),
            ("1d", "Day"),
            ("day", "Day"),
            ("1w", "Week"),
            ("week", "Week"),
            ("1M", "Month"),
            ("month", "Month"),
            ("quarter", "Quarter"),
            ("year", "Year"),
        ],
    )
    def test_period_map(self, key, expected):
        assert PERIOD_MAP[key] == expected

    def test_period_map_missing_key(self):
        assert "invalid" not in PERIOD_MAP

    @pytest.mark.parametrize("key,expected", [("HK", "HK"), ("US", "US"), ("CN", "CN"), ("SG", "SG")])
    def test_market_map(self, key, expected):
        assert MARKET_MAP[key] == expected

    def test_market_map_missing_key(self):
        assert "XX" not in MARKET_MAP

    def test_adjust_map(self):
        assert "none" in ADJUST_MAP
        assert "forward" in ADJUST_MAP

    def test_order_side_map(self):
        assert set(ORDER_SIDE_MAP.keys()) == {"Buy", "Sell"}

    def test_order_type_map(self):
        assert "LO" in ORDER_TYPE_MAP
        assert "MO" in ORDER_TYPE_MAP
        assert "ELO" in ORDER_TYPE_MAP

    def test_time_in_force_map(self):
        assert set(TIME_IN_FORCE_MAP.keys()) == {"Day", "GoodTilCanceled", "GoodTilDate"}

    def test_outside_rth_map(self):
        assert set(OUTSIDE_RTH_MAP.keys()) == {"RTHOnly", "AnyTime", "Overnight"}

    def test_order_status_map(self):
        assert "Filled" in ORDER_STATUS_MAP
        assert "Canceled" in ORDER_STATUS_MAP
        assert len(ORDER_STATUS_MAP) == 14

    def test_warrant_sort_by_map(self):
        assert "LastDone" in WARRANT_SORT_BY_MAP
        assert "Volume" in WARRANT_SORT_BY_MAP

    def test_sort_order_map(self):
        assert set(SORT_ORDER_MAP.keys()) == {"Ascending", "Descending"}

    def test_update_mode_map(self):
        assert set(UPDATE_MODE_MAP.keys()) == {"Add", "Remove", "Replace"}

    def test_calc_index_map(self):
        assert "LastDone" in CALC_INDEX_MAP
        assert "PeTtmRatio" in CALC_INDEX_MAP
        assert "Delta" in CALC_INDEX_MAP


# ── Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def mock_quote_ctx():
    return MagicMock()


@pytest.fixture
def mock_trade_ctx():
    return MagicMock()


@pytest.fixture
def mock_content_ctx():
    return MagicMock()


@pytest.fixture
def quote_tools(mock_quote_ctx):
    """LongbridgeTools with only quote + candlesticks enabled."""
    with patch.dict(
        "os.environ", {"LONGBRIDGE_APP_KEY": "k", "LONGBRIDGE_APP_SECRET": "s", "LONGBRIDGE_ACCESS_TOKEN": "t"}
    ):
        tools = LongbridgeTools(enable_quote=True, enable_candlesticks=True)
        tools._quote_ctx = mock_quote_ctx
        return tools


@pytest.fixture
def trade_tools(mock_trade_ctx):
    """LongbridgeTools with only trade enabled."""
    with patch.dict(
        "os.environ", {"LONGBRIDGE_APP_KEY": "k", "LONGBRIDGE_APP_SECRET": "s", "LONGBRIDGE_ACCESS_TOKEN": "t"}
    ):
        tools = LongbridgeTools(enable_quote=False, enable_candlesticks=False, enable_trade=True)
        tools._trade_ctx = mock_trade_ctx
        return tools


@pytest.fixture
def content_tools(mock_content_ctx):
    """LongbridgeTools with only content enabled."""
    with patch.dict(
        "os.environ", {"LONGBRIDGE_APP_KEY": "k", "LONGBRIDGE_APP_SECRET": "s", "LONGBRIDGE_ACCESS_TOKEN": "t"}
    ):
        tools = LongbridgeTools(enable_quote=False, enable_candlesticks=False, enable_content=True)
        tools._content_ctx = mock_content_ctx
        return tools


@pytest.fixture
def all_tools(mock_quote_ctx, mock_trade_ctx, mock_content_ctx):
    """LongbridgeTools with all tools enabled."""
    with patch.dict(
        "os.environ", {"LONGBRIDGE_APP_KEY": "k", "LONGBRIDGE_APP_SECRET": "s", "LONGBRIDGE_ACCESS_TOKEN": "t"}
    ):
        tools = LongbridgeTools(all=True)
        tools._quote_ctx = mock_quote_ctx
        tools._trade_ctx = mock_trade_ctx
        tools._content_ctx = mock_content_ctx
        return tools


# ── Initialization Tests ────────────────────────────────────────


class TestInitialization:
    def test_default_enables_quote_and_candlesticks(self):
        with patch.dict(
            "os.environ", {"LONGBRIDGE_APP_KEY": "k", "LONGBRIDGE_APP_SECRET": "s", "LONGBRIDGE_ACCESS_TOKEN": "t"}
        ):
            tools = LongbridgeTools()
            fn_names = list(tools.functions.keys())
            assert "get_quote" in fn_names
            assert "get_static_info" in fn_names
            assert "get_depth" in fn_names
            assert "get_candlesticks" in fn_names
            assert "get_history_candlesticks" in fn_names
            # Trade should NOT be enabled by default
            assert "submit_order" not in fn_names
            assert "get_news" not in fn_names

    def test_all_flag_enables_everything(self):
        with patch.dict(
            "os.environ", {"LONGBRIDGE_APP_KEY": "k", "LONGBRIDGE_APP_SECRET": "s", "LONGBRIDGE_ACCESS_TOKEN": "t"}
        ):
            tools = LongbridgeTools(all=True)
            fn_names = list(tools.functions.keys())
            assert "get_quote" in fn_names
            assert "get_candlesticks" in fn_names
            assert "get_calc_indexes" in fn_names
            assert "get_option_chain_expiry_dates" in fn_names
            assert "get_warrant_issuers" in fn_names
            assert "get_trading_session" in fn_names
            assert "get_watchlist" in fn_names
            assert "submit_order" in fn_names
            assert "get_news" in fn_names
            assert "get_topics" in fn_names

    def test_all_overrides_individual_false(self):
        with patch.dict(
            "os.environ", {"LONGBRIDGE_APP_KEY": "k", "LONGBRIDGE_APP_SECRET": "s", "LONGBRIDGE_ACCESS_TOKEN": "t"}
        ):
            tools = LongbridgeTools(all=True, enable_quote=False, enable_trade=False)
            fn_names = list(tools.functions.keys())
            assert "get_quote" in fn_names
            assert "submit_order" in fn_names

    def test_selective_enable(self):
        with patch.dict(
            "os.environ", {"LONGBRIDGE_APP_KEY": "k", "LONGBRIDGE_APP_SECRET": "s", "LONGBRIDGE_ACCESS_TOKEN": "t"}
        ):
            tools = LongbridgeTools(
                enable_quote=False,
                enable_candlesticks=False,
                enable_options=True,
                enable_content=True,
            )
            fn_names = list(tools.functions.keys())
            assert "get_quote" not in fn_names
            assert "get_candlesticks" not in fn_names
            assert "get_option_chain_expiry_dates" in fn_names
            assert "get_option_chain_info" in fn_names
            assert "get_option_quote" in fn_names
            assert "get_news" in fn_names
            assert "get_topics" in fn_names

    def test_explicit_credentials(self):
        tools = LongbridgeTools(
            app_key="my_key",
            app_secret="my_secret",
            access_token="my_token",
        )
        assert tools._app_key == "my_key"
        assert tools._app_secret == "my_secret"
        assert tools._access_token == "my_token"

    def test_env_var_credentials(self):
        with patch.dict(
            "os.environ",
            {"LONGBRIDGE_APP_KEY": "env_k", "LONGBRIDGE_APP_SECRET": "env_s", "LONGBRIDGE_ACCESS_TOKEN": "env_t"},
        ):
            tools = LongbridgeTools()
            assert tools._app_key == "env_k"
            assert tools._app_secret == "env_s"
            assert tools._access_token == "env_t"

    def test_toolkit_name(self):
        with patch.dict(
            "os.environ", {"LONGBRIDGE_APP_KEY": "k", "LONGBRIDGE_APP_SECRET": "s", "LONGBRIDGE_ACCESS_TOKEN": "t"}
        ):
            tools = LongbridgeTools()
            assert tools.name == "longbridge_tools"

    def test_quote_tool_count(self):
        with patch.dict(
            "os.environ", {"LONGBRIDGE_APP_KEY": "k", "LONGBRIDGE_APP_SECRET": "s", "LONGBRIDGE_ACCESS_TOKEN": "t"}
        ):
            tools = LongbridgeTools(enable_quote=True, enable_candlesticks=False)
            assert len(tools.functions) == 8

    def test_trade_tool_count(self):
        with patch.dict(
            "os.environ", {"LONGBRIDGE_APP_KEY": "k", "LONGBRIDGE_APP_SECRET": "s", "LONGBRIDGE_ACCESS_TOKEN": "t"}
        ):
            tools = LongbridgeTools(enable_quote=False, enable_candlesticks=False, enable_trade=True)
            assert len(tools.functions) == 14

    def test_content_tool_count(self):
        with patch.dict(
            "os.environ", {"LONGBRIDGE_APP_KEY": "k", "LONGBRIDGE_APP_SECRET": "s", "LONGBRIDGE_ACCESS_TOKEN": "t"}
        ):
            tools = LongbridgeTools(enable_quote=False, enable_candlesticks=False, enable_content=True)
            assert len(tools.functions) == 2

    def test_watchlist_tool_count(self):
        with patch.dict(
            "os.environ", {"LONGBRIDGE_APP_KEY": "k", "LONGBRIDGE_APP_SECRET": "s", "LONGBRIDGE_ACCESS_TOKEN": "t"}
        ):
            tools = LongbridgeTools(enable_quote=False, enable_candlesticks=False, enable_watchlist=True)
            assert len(tools.functions) == 4

    def test_market_info_tool_count(self):
        with patch.dict(
            "os.environ", {"LONGBRIDGE_APP_KEY": "k", "LONGBRIDGE_APP_SECRET": "s", "LONGBRIDGE_ACCESS_TOKEN": "t"}
        ):
            tools = LongbridgeTools(enable_quote=False, enable_candlesticks=False, enable_market_info=True)
            assert len(tools.functions) == 6

    def test_options_tool_count(self):
        with patch.dict(
            "os.environ", {"LONGBRIDGE_APP_KEY": "k", "LONGBRIDGE_APP_SECRET": "s", "LONGBRIDGE_ACCESS_TOKEN": "t"}
        ):
            tools = LongbridgeTools(enable_quote=False, enable_candlesticks=False, enable_options=True)
            assert len(tools.functions) == 3

    def test_warrants_tool_count(self):
        with patch.dict(
            "os.environ", {"LONGBRIDGE_APP_KEY": "k", "LONGBRIDGE_APP_SECRET": "s", "LONGBRIDGE_ACCESS_TOKEN": "t"}
        ):
            tools = LongbridgeTools(enable_quote=False, enable_candlesticks=False, enable_warrants=True)
            assert len(tools.functions) == 3

    def test_no_tools_enabled(self):
        with patch.dict(
            "os.environ", {"LONGBRIDGE_APP_KEY": "k", "LONGBRIDGE_APP_SECRET": "s", "LONGBRIDGE_ACCESS_TOKEN": "t"}
        ):
            tools = LongbridgeTools(enable_quote=False, enable_candlesticks=False)
            assert len(tools.functions) == 0


# ── Config & Context Lazy Loading ───────────────────────────────


class TestLazyLoading:
    def test_config_from_explicit_keys(self):
        tools = LongbridgeTools(app_key="k", app_secret="s", access_token="t")
        _mock_openapi.Config.from_apikey.return_value = "config_obj"
        result = tools.config
        _mock_openapi.Config.from_apikey.assert_called_with("k", "s", "t")
        assert result == "config_obj"

    def test_config_from_env(self):
        with patch.dict("os.environ", {}, clear=False):
            tools = LongbridgeTools()
            tools._app_key = None
            tools._app_secret = None
            tools._access_token = None
            _mock_openapi.Config.from_apikey_env.return_value = "env_config"
            result = tools.config
            _mock_openapi.Config.from_apikey_env.assert_called()
            assert result == "env_config"

    def test_config_cached(self):
        tools = LongbridgeTools(app_key="k", app_secret="s", access_token="t")
        _mock_openapi.Config.from_apikey.return_value = "cfg"
        c1 = tools.config
        c2 = tools.config
        assert c1 is c2

    def test_quote_ctx_lazy(self):
        tools = LongbridgeTools(app_key="k", app_secret="s", access_token="t")
        tools._config = "mock_config"
        mock_ctx = MagicMock()
        _mock_openapi.QuoteContext.return_value = mock_ctx
        result = tools.quote_ctx
        _mock_openapi.QuoteContext.assert_called_with("mock_config")
        assert result is mock_ctx

    def test_trade_ctx_lazy(self):
        tools = LongbridgeTools(app_key="k", app_secret="s", access_token="t")
        tools._config = "mock_config"
        mock_ctx = MagicMock()
        _mock_openapi.TradeContext.return_value = mock_ctx
        result = tools.trade_ctx
        _mock_openapi.TradeContext.assert_called_with("mock_config")
        assert result is mock_ctx

    def test_content_ctx_lazy(self):
        tools = LongbridgeTools(app_key="k", app_secret="s", access_token="t")
        tools._config = "mock_config"
        mock_ctx = MagicMock()
        _mock_openapi.ContentContext.return_value = mock_ctx
        result = tools.content_ctx
        _mock_openapi.ContentContext.assert_called_with("mock_config")
        assert result is mock_ctx

    def test_context_cached(self):
        tools = LongbridgeTools(app_key="k", app_secret="s", access_token="t")
        tools._config = "mock_config"
        _mock_openapi.QuoteContext.return_value = MagicMock()
        c1 = tools.quote_ctx
        c2 = tools.quote_ctx
        assert c1 is c2


# ── Quote Tool Tests ────────────────────────────────────────────


class TestQuoteTools:
    def test_get_quote_success(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.quote.return_value = [Mock(symbol="700.HK", last_done=Decimal("350"), volume=1000000)]
        result = quote_tools.get_quote("700.HK,AAPL.US")
        data = json.loads(result)
        assert isinstance(data, list)
        mock_quote_ctx.quote.assert_called_once_with(["700.HK", "AAPL.US"])

    def test_get_quote_single_symbol(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.quote.return_value = [Mock(symbol="TSLA.US")]
        result = quote_tools.get_quote("TSLA.US")
        mock_quote_ctx.quote.assert_called_once_with(["TSLA.US"])
        assert "Error" not in result

    def test_get_quote_api_error(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.quote.side_effect = MockOpenApiException(code=400, message="Bad request")
        result = quote_tools.get_quote("INVALID.XX")
        assert "Error fetching quotes" in result
        assert "code=400" in result

    def test_get_quote_generic_error(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.quote.side_effect = Exception("Network error")
        result = quote_tools.get_quote("700.HK")
        assert "Error fetching quotes" in result
        assert "Network error" in result

    def test_get_static_info(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.static_info.return_value = [Mock(symbol="700.HK", name_en="Tencent")]
        result = quote_tools.get_static_info("700.HK")
        mock_quote_ctx.static_info.assert_called_once_with(["700.HK"])
        assert "Error" not in result

    def test_get_static_info_error(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.static_info.side_effect = MockOpenApiException(code=500, message="Server error")
        result = quote_tools.get_static_info("700.HK")
        assert "Error fetching static info" in result

    def test_get_depth(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.depth.return_value = Mock(asks=[], bids=[])
        result = quote_tools.get_depth("700.HK")
        mock_quote_ctx.depth.assert_called_once_with("700.HK")
        assert "Error" not in result

    def test_get_depth_error(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.depth.side_effect = Exception("Connection lost")
        result = quote_tools.get_depth("700.HK")
        assert "Error fetching depth" in result

    def test_get_brokers(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.brokers.return_value = Mock(ask_brokers=[], bid_brokers=[])
        result = quote_tools.get_brokers("700.HK")
        mock_quote_ctx.brokers.assert_called_once_with("700.HK")
        assert "Error" not in result

    def test_get_brokers_error(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.brokers.side_effect = MockOpenApiException(code=403, message="Forbidden")
        result = quote_tools.get_brokers("700.HK")
        assert "Error fetching brokers" in result

    def test_get_trades(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.trades.return_value = [Mock(price=Decimal("350"), volume=100)]
        result = quote_tools.get_trades("700.HK", count=10)
        mock_quote_ctx.trades.assert_called_once_with("700.HK", 10)
        assert "Error" not in result

    def test_get_trades_default_count(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.trades.return_value = []
        quote_tools.get_trades("700.HK")
        mock_quote_ctx.trades.assert_called_once_with("700.HK", 50)

    def test_get_trades_error(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.trades.side_effect = Exception("Timeout")
        result = quote_tools.get_trades("700.HK")
        assert "Error fetching trades" in result

    def test_get_intraday(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.intraday.return_value = [Mock(price=Decimal("350"))]
        result = quote_tools.get_intraday("700.HK")
        mock_quote_ctx.intraday.assert_called_once_with("700.HK")
        assert "Error" not in result

    def test_get_intraday_error(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.intraday.side_effect = MockOpenApiException(code=429, message="Rate limit")
        result = quote_tools.get_intraday("700.HK")
        assert "Error fetching intraday" in result

    def test_get_participants(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.participants.return_value = [Mock(name="Broker A")]
        result = quote_tools.get_participants()
        mock_quote_ctx.participants.assert_called_once()
        assert "Error" not in result

    def test_get_participants_error(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.participants.side_effect = Exception("Failed")
        result = quote_tools.get_participants()
        assert "Error fetching participants" in result

    def test_get_filings(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.filings.return_value = [Mock(title="Annual Report")]
        result = quote_tools.get_filings("700.HK")
        mock_quote_ctx.filings.assert_called_once_with("700.HK")
        assert "Error" not in result

    def test_get_filings_error(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.filings.side_effect = MockOpenApiException(code=404, message="Not found")
        result = quote_tools.get_filings("UNKNOWN.XX")
        assert "Error fetching filings" in result


# ── Candlestick Tool Tests ──────────────────────────────────────


class TestCandlestickTools:
    def test_get_candlesticks_default(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.candlesticks.return_value = [
            Mock(open=Decimal("340"), close=Decimal("350"), high=Decimal("360"), low=Decimal("335"))
        ]
        result = quote_tools.get_candlesticks("700.HK")
        mock_quote_ctx.candlesticks.assert_called_once_with("700.HK", "Day", 100, "NoAdjust")
        assert "Error" not in result

    def test_get_candlesticks_with_period(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.candlesticks.return_value = []
        quote_tools.get_candlesticks("700.HK", period="5m", count=50, adjust="forward")
        mock_quote_ctx.candlesticks.assert_called_once_with("700.HK", "Min_5", 50, "ForwardAdjust")

    def test_get_candlesticks_invalid_period(self, quote_tools):
        result = quote_tools.get_candlesticks("700.HK", period="invalid")
        assert "Error fetching candlesticks" in result

    def test_get_candlesticks_api_error(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.candlesticks.side_effect = MockOpenApiException(code=500, message="Server error")
        result = quote_tools.get_candlesticks("700.HK")
        assert "Error fetching candlesticks" in result
        assert "code=500" in result

    def test_get_history_candlesticks(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.history_candlesticks_by_date.return_value = [Mock(close=Decimal("350"))]
        result = quote_tools.get_history_candlesticks("700.HK", "2024-01-01", "2024-06-01")
        mock_quote_ctx.history_candlesticks_by_date.assert_called_once_with(
            "700.HK", "Day", "NoAdjust", start=date(2024, 1, 1), end=date(2024, 6, 1)
        )
        assert "Error" not in result

    def test_get_history_candlesticks_forward_adjust(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.history_candlesticks_by_date.return_value = []
        quote_tools.get_history_candlesticks("700.HK", "2024-01-01", "2024-06-01", period="1w", adjust="forward")
        mock_quote_ctx.history_candlesticks_by_date.assert_called_once_with(
            "700.HK", "Week", "ForwardAdjust", start=date(2024, 1, 1), end=date(2024, 6, 1)
        )

    def test_get_history_candlesticks_invalid_date(self, quote_tools):
        result = quote_tools.get_history_candlesticks("700.HK", "bad-date", "2024-06-01")
        assert "Error fetching history candlesticks" in result

    def test_get_history_candlesticks_api_error(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.history_candlesticks_by_date.side_effect = MockOpenApiException(code=400, message="Bad range")
        result = quote_tools.get_history_candlesticks("700.HK", "2024-01-01", "2024-06-01")
        assert "Error fetching history candlesticks" in result


# ── Calc Indexes Tests ──────────────────────────────────────────


class TestCalcIndexes:
    def test_get_calc_indexes_success(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.calc_indexes.return_value = [Mock(symbol="700.HK")]
        result = all_tools.get_calc_indexes("700.HK,AAPL.US", "LastDone,PeTtmRatio")
        data = json.loads(result)
        assert isinstance(data, list)
        mock_quote_ctx.calc_indexes.assert_called_once()
        call_args = mock_quote_ctx.calc_indexes.call_args
        assert call_args[0][0] == ["700.HK", "AAPL.US"]
        assert call_args[0][1] == ["LastDone", "PeTtmRatio"]

    def test_get_calc_indexes_unknown_index(self, all_tools):
        result = all_tools.get_calc_indexes("700.HK", "InvalidIndex")
        assert "Unknown index" in result
        assert "InvalidIndex" in result

    def test_get_calc_indexes_api_error(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.calc_indexes.side_effect = MockOpenApiException(code=500, message="Calc failed")
        result = all_tools.get_calc_indexes("700.HK", "LastDone")
        assert "Error fetching calc indexes" in result


# ── Options Tool Tests ──────────────────────────────────────────


class TestOptionsTools:
    def test_get_option_chain_expiry_dates(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.option_chain_expiry_date_list.return_value = [date(2024, 3, 17), date(2024, 6, 21)]
        result = all_tools.get_option_chain_expiry_dates("AAPL.US")
        mock_quote_ctx.option_chain_expiry_date_list.assert_called_once_with("AAPL.US")
        data = json.loads(result)
        assert len(data) == 2

    def test_get_option_chain_expiry_dates_error(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.option_chain_expiry_date_list.side_effect = Exception("Failed")
        result = all_tools.get_option_chain_expiry_dates("AAPL.US")
        assert "Error fetching option chain dates" in result

    def test_get_option_chain_info(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.option_chain_info_by_date.return_value = [Mock(price=Decimal("150"))]
        result = all_tools.get_option_chain_info("AAPL.US", "2024-03-17")
        mock_quote_ctx.option_chain_info_by_date.assert_called_once_with("AAPL.US", date(2024, 3, 17))
        assert "Error" not in result

    def test_get_option_chain_info_error(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.option_chain_info_by_date.side_effect = MockOpenApiException(code=400, message="Invalid date")
        result = all_tools.get_option_chain_info("AAPL.US", "2024-03-17")
        assert "Error fetching option chain info" in result

    def test_get_option_quote(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.option_quote.return_value = [Mock(symbol="AAPL230317P160000.US")]
        result = all_tools.get_option_quote("AAPL230317P160000.US")
        mock_quote_ctx.option_quote.assert_called_once_with(["AAPL230317P160000.US"])
        assert "Error" not in result

    def test_get_option_quote_error(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.option_quote.side_effect = Exception("Timeout")
        result = all_tools.get_option_quote("AAPL230317P160000.US")
        assert "Error fetching option quotes" in result


# ── Warrants Tool Tests ─────────────────────────────────────────


class TestWarrantsTools:
    def test_get_warrant_issuers(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.warrant_issuers.return_value = [Mock(name="Issuer A")]
        result = all_tools.get_warrant_issuers()
        mock_quote_ctx.warrant_issuers.assert_called_once()
        assert "Error" not in result

    def test_get_warrant_issuers_error(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.warrant_issuers.side_effect = MockOpenApiException(code=500, message="Fail")
        result = all_tools.get_warrant_issuers()
        assert "Error fetching warrant issuers" in result

    def test_get_warrant_list(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.warrant_list.return_value = [Mock(symbol="21125.HK")]
        result = all_tools.get_warrant_list("700.HK")
        mock_quote_ctx.warrant_list.assert_called_once_with("700.HK", sort_by="LastDone", sort_order="Ascending")
        assert "Error" not in result

    def test_get_warrant_list_with_sort(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.warrant_list.return_value = []
        all_tools.get_warrant_list("700.HK", sort_by="Volume", sort_order="Descending")
        mock_quote_ctx.warrant_list.assert_called_once_with("700.HK", sort_by="Volume", sort_order="Descending")

    def test_get_warrant_list_error(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.warrant_list.side_effect = Exception("Fail")
        result = all_tools.get_warrant_list("700.HK")
        assert "Error fetching warrant list" in result

    def test_get_warrant_quote(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.warrant_quote.return_value = [Mock(symbol="21125.HK")]
        result = all_tools.get_warrant_quote("21125.HK,21126.HK")
        mock_quote_ctx.warrant_quote.assert_called_once_with(["21125.HK", "21126.HK"])
        assert "Error" not in result

    def test_get_warrant_quote_error(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.warrant_quote.side_effect = MockOpenApiException(code=404, message="Not found")
        result = all_tools.get_warrant_quote("INVALID.HK")
        assert "Error fetching warrant quotes" in result


# ── Market Info Tool Tests ──────────────────────────────────────


class TestMarketInfoTools:
    def test_get_trading_session(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.trading_session.return_value = [Mock(market="HK")]
        result = all_tools.get_trading_session()
        mock_quote_ctx.trading_session.assert_called_once()
        assert "Error" not in result

    def test_get_trading_session_error(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.trading_session.side_effect = Exception("Failed")
        result = all_tools.get_trading_session()
        assert "Error fetching trading sessions" in result

    def test_get_trading_days(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.trading_days.return_value = Mock(trading_days=[], half_trading_days=[])
        result = all_tools.get_trading_days("HK", "2024-01-01", "2024-01-31")
        mock_quote_ctx.trading_days.assert_called_once_with("HK", date(2024, 1, 1), date(2024, 1, 31))
        assert "Error" not in result

    def test_get_trading_days_invalid_market(self, all_tools):
        result = all_tools.get_trading_days("XX", "2024-01-01", "2024-01-31")
        assert "Error fetching trading days" in result

    def test_get_trading_days_error(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.trading_days.side_effect = MockOpenApiException(code=400, message="Too wide")
        result = all_tools.get_trading_days("HK", "2024-01-01", "2024-12-31")
        assert "Error fetching trading days" in result

    def test_get_capital_flow(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.capital_flow.return_value = [Mock(inflow=Decimal("1000000"))]
        result = all_tools.get_capital_flow("700.HK")
        mock_quote_ctx.capital_flow.assert_called_once_with("700.HK")
        assert "Error" not in result

    def test_get_capital_flow_error(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.capital_flow.side_effect = Exception("Timeout")
        result = all_tools.get_capital_flow("700.HK")
        assert "Error fetching capital flow" in result

    def test_get_capital_distribution(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.capital_distribution.return_value = Mock(large=Decimal("5000000"))
        result = all_tools.get_capital_distribution("700.HK")
        mock_quote_ctx.capital_distribution.assert_called_once_with("700.HK")
        assert "Error" not in result

    def test_get_capital_distribution_error(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.capital_distribution.side_effect = MockOpenApiException(code=500, message="Error")
        result = all_tools.get_capital_distribution("700.HK")
        assert "Error fetching capital distribution" in result

    def test_get_market_temperature(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.market_temperature.return_value = Mock(temperature=65)
        result = all_tools.get_market_temperature("HK")
        mock_quote_ctx.market_temperature.assert_called_once_with("HK")
        assert "Error" not in result

    def test_get_market_temperature_invalid_market(self, all_tools):
        result = all_tools.get_market_temperature("XX")
        assert "Error fetching market temperature" in result

    def test_get_security_list(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.security_list.return_value = [Mock(symbol="700.HK")]
        result = all_tools.get_security_list("HK")
        mock_quote_ctx.security_list.assert_called_once_with("HK")
        assert "Error" not in result

    def test_get_security_list_error(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.security_list.side_effect = Exception("Failed")
        result = all_tools.get_security_list("US")
        assert "Error fetching security list" in result


# ── Watchlist Tool Tests ────────────────────────────────────────


class TestWatchlistTools:
    def test_get_watchlist(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.watchlist.return_value = [Mock(name="My Group")]
        result = all_tools.get_watchlist()
        mock_quote_ctx.watchlist.assert_called_once()
        assert "Error" not in result

    def test_get_watchlist_error(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.watchlist.side_effect = MockOpenApiException(code=401, message="Unauthorized")
        result = all_tools.get_watchlist()
        assert "Error fetching watchlist" in result

    def test_create_watchlist_group(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.create_watchlist_group.return_value = 12345
        result = all_tools.create_watchlist_group("My Group", "700.HK,AAPL.US")
        data = json.loads(result)
        assert data["group_id"] == 12345
        mock_quote_ctx.create_watchlist_group.assert_called_once_with("My Group", securities=["700.HK", "AAPL.US"])

    def test_create_watchlist_group_no_securities(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.create_watchlist_group.return_value = 99
        result = all_tools.create_watchlist_group("Empty Group")
        data = json.loads(result)
        assert data["group_id"] == 99
        mock_quote_ctx.create_watchlist_group.assert_called_once_with("Empty Group", securities=None)

    def test_create_watchlist_group_error(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.create_watchlist_group.side_effect = Exception("Failed")
        result = all_tools.create_watchlist_group("Bad Group")
        assert "Error creating watchlist group" in result

    def test_update_watchlist_group(self, all_tools, mock_quote_ctx):
        result = all_tools.update_watchlist_group(123, name="New Name", securities="TSLA.US", mode="Add")
        data = json.loads(result)
        assert data["status"] == "success"
        assert data["group_id"] == 123

    def test_update_watchlist_group_no_name(self, all_tools, mock_quote_ctx):
        all_tools.update_watchlist_group(123, securities="TSLA.US", mode="Replace")
        mock_quote_ctx.update_watchlist_group.assert_called_once_with(
            123, name=None, securities=["TSLA.US"], mode="Replace"
        )

    def test_update_watchlist_group_error(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.update_watchlist_group.side_effect = MockOpenApiException(code=404, message="Not found")
        result = all_tools.update_watchlist_group(999)
        assert "Error updating watchlist group" in result

    def test_delete_watchlist_group(self, all_tools, mock_quote_ctx):
        result = all_tools.delete_watchlist_group(123, purge=True)
        data = json.loads(result)
        assert data["status"] == "success"
        assert data["purged"] is True
        mock_quote_ctx.delete_watchlist_group.assert_called_once_with(123, purge=True)

    def test_delete_watchlist_group_error(self, all_tools, mock_quote_ctx):
        mock_quote_ctx.delete_watchlist_group.side_effect = Exception("Cannot delete")
        result = all_tools.delete_watchlist_group(123)
        assert "Error deleting watchlist group" in result


# ── Trade Tool Tests ────────────────────────────────────────────


class TestTradeTools:
    def test_submit_order_limit(self, trade_tools, mock_trade_ctx):
        mock_resp = Mock()
        mock_resp.order_id = "ORD123456"
        mock_trade_ctx.submit_order.return_value = mock_resp

        result = trade_tools.submit_order(
            symbol="700.HK",
            side="Buy",
            order_type="LO",
            quantity="200",
            price="50.00",
            remark="test order",
        )
        data = json.loads(result)
        assert data["order_id"] == "ORD123456"

        call_kwargs = mock_trade_ctx.submit_order.call_args[1]
        assert call_kwargs["symbol"] == "700.HK"
        assert call_kwargs["side"] == "Buy"
        assert call_kwargs["order_type"] == "LO"
        assert call_kwargs["submitted_quantity"] == Decimal("200")
        assert call_kwargs["submitted_price"] == Decimal("50.00")
        assert call_kwargs["remark"] == "test order"

    def test_submit_order_market(self, trade_tools, mock_trade_ctx):
        mock_resp = Mock()
        mock_resp.order_id = "ORD789"
        mock_trade_ctx.submit_order.return_value = mock_resp

        result = trade_tools.submit_order(
            symbol="AAPL.US",
            side="Sell",
            order_type="MO",
            quantity="100",
        )
        data = json.loads(result)
        assert data["order_id"] == "ORD789"
        call_kwargs = mock_trade_ctx.submit_order.call_args[1]
        assert call_kwargs["submitted_price"] is None

    def test_submit_order_with_trigger(self, trade_tools, mock_trade_ctx):
        mock_resp = Mock()
        mock_resp.order_id = "ORD_LIT"
        mock_trade_ctx.submit_order.return_value = mock_resp

        trade_tools.submit_order(
            symbol="700.HK",
            side="Buy",
            order_type="LIT",
            quantity="100",
            price="350",
            trigger_price="340",
        )
        call_kwargs = mock_trade_ctx.submit_order.call_args[1]
        assert call_kwargs["trigger_price"] == Decimal("340")
        assert call_kwargs["submitted_price"] == Decimal("350")

    def test_submit_order_with_expire_date(self, trade_tools, mock_trade_ctx):
        mock_resp = Mock()
        mock_resp.order_id = "ORD_GTD"
        mock_trade_ctx.submit_order.return_value = mock_resp

        trade_tools.submit_order(
            symbol="700.HK",
            side="Buy",
            order_type="LO",
            quantity="100",
            price="350",
            time_in_force="GoodTilDate",
            expire_date="2024-12-31",
        )
        call_kwargs = mock_trade_ctx.submit_order.call_args[1]
        assert call_kwargs["time_in_force"] == "GoodTilDate"
        assert call_kwargs["expire_date"] == date(2024, 12, 31)

    def test_submit_order_with_outside_rth(self, trade_tools, mock_trade_ctx):
        mock_resp = Mock()
        mock_resp.order_id = "ORD_RTH"
        mock_trade_ctx.submit_order.return_value = mock_resp

        trade_tools.submit_order(
            symbol="AAPL.US",
            side="Buy",
            order_type="LO",
            quantity="100",
            price="150",
            outside_rth="AnyTime",
        )
        call_kwargs = mock_trade_ctx.submit_order.call_args[1]
        assert call_kwargs["outside_rth"] == "AnyTime"

    def test_submit_order_api_error(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.submit_order.side_effect = MockOpenApiException(code=400, message="Insufficient funds")
        result = trade_tools.submit_order(symbol="700.HK", side="Buy", order_type="LO", quantity="999999", price="350")
        assert "Error submitting order" in result
        assert "Insufficient funds" in result

    def test_submit_order_invalid_side(self, trade_tools):
        result = trade_tools.submit_order(symbol="700.HK", side="Invalid", order_type="LO", quantity="100", price="350")
        assert "Error submitting order" in result

    def test_replace_order(self, trade_tools, mock_trade_ctx):
        result = trade_tools.replace_order("ORD123", "100", "355.00")
        data = json.loads(result)
        assert data["status"] == "success"
        assert data["order_id"] == "ORD123"
        mock_trade_ctx.replace_order.assert_called_once_with(
            order_id="ORD123", quantity=Decimal("100"), price=Decimal("355.00")
        )

    def test_replace_order_error(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.replace_order.side_effect = MockOpenApiException(code=400, message="Order not found")
        result = trade_tools.replace_order("INVALID_ID", "100", "350")
        assert "Error replacing order" in result

    def test_cancel_order(self, trade_tools, mock_trade_ctx):
        result = trade_tools.cancel_order("ORD123")
        data = json.loads(result)
        assert data["status"] == "success"
        mock_trade_ctx.cancel_order.assert_called_once_with("ORD123")

    def test_cancel_order_error(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.cancel_order.side_effect = MockOpenApiException(code=400, message="Already filled")
        result = trade_tools.cancel_order("ORD_FILLED")
        assert "Error canceling order" in result

    def test_get_today_orders(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.today_orders.return_value = [Mock(order_id="ORD1"), Mock(order_id="ORD2")]
        result = trade_tools.get_today_orders()
        data = json.loads(result)
        assert len(data) == 2
        mock_trade_ctx.today_orders.assert_called_once_with(symbol=None, status=None)

    def test_get_today_orders_with_filter(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.today_orders.return_value = []
        trade_tools.get_today_orders(symbol="700.HK", status="Filled,New")
        call_kwargs = mock_trade_ctx.today_orders.call_args[1]
        assert call_kwargs["symbol"] == "700.HK"
        assert call_kwargs["status"] == ["Filled", "New"]

    def test_get_today_orders_error(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.today_orders.side_effect = Exception("Timeout")
        result = trade_tools.get_today_orders()
        assert "Error fetching today's orders" in result

    def test_get_history_orders(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.history_orders.return_value = [Mock(order_id="HIST1")]
        result = trade_tools.get_history_orders("2024-01-01", "2024-06-30")
        data = json.loads(result)
        assert len(data) == 1
        call_kwargs = mock_trade_ctx.history_orders.call_args[1]
        assert call_kwargs["start_at"] == datetime(2024, 1, 1)
        assert call_kwargs["end_at"] == datetime(2024, 6, 30)

    def test_get_history_orders_with_filter(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.history_orders.return_value = []
        trade_tools.get_history_orders("2024-01-01", "2024-06-30", symbol="700.HK", status="Filled")
        call_kwargs = mock_trade_ctx.history_orders.call_args[1]
        assert call_kwargs["symbol"] == "700.HK"
        assert call_kwargs["status"] == ["Filled"]

    def test_get_history_orders_error(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.history_orders.side_effect = MockOpenApiException(code=500, message="Error")
        result = trade_tools.get_history_orders("2024-01-01", "2024-06-30")
        assert "Error fetching history orders" in result

    def test_get_order_detail(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.order_detail.return_value = Mock(order_id="ORD123", symbol="700.HK")
        result = trade_tools.get_order_detail("ORD123")
        mock_trade_ctx.order_detail.assert_called_once_with("ORD123")
        assert "Error" not in result

    def test_get_order_detail_error(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.order_detail.side_effect = MockOpenApiException(code=404, message="Not found")
        result = trade_tools.get_order_detail("INVALID")
        assert "Error fetching order detail" in result

    def test_get_today_executions(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.today_executions.return_value = [Mock(trade_id="T1")]
        result = trade_tools.get_today_executions()
        assert "Error" not in result
        mock_trade_ctx.today_executions.assert_called_once_with(symbol=None, order_id=None)

    def test_get_today_executions_with_filter(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.today_executions.return_value = []
        trade_tools.get_today_executions(symbol="700.HK", order_id="ORD1")
        call_kwargs = mock_trade_ctx.today_executions.call_args[1]
        assert call_kwargs["symbol"] == "700.HK"
        assert call_kwargs["order_id"] == "ORD1"

    def test_get_today_executions_error(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.today_executions.side_effect = Exception("Error")
        result = trade_tools.get_today_executions()
        assert "Error fetching today's executions" in result

    def test_get_history_executions(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.history_executions.return_value = [Mock(trade_id="HT1")]
        result = trade_tools.get_history_executions("2024-01-01", "2024-06-30")
        assert "Error" not in result

    def test_get_history_executions_with_symbol(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.history_executions.return_value = []
        trade_tools.get_history_executions("2024-01-01", "2024-06-30", symbol="700.HK")
        call_kwargs = mock_trade_ctx.history_executions.call_args[1]
        assert call_kwargs["symbol"] == "700.HK"

    def test_get_history_executions_error(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.history_executions.side_effect = MockOpenApiException(code=500, message="Fail")
        result = trade_tools.get_history_executions("2024-01-01", "2024-06-30")
        assert "Error fetching history executions" in result

    def test_get_account_balance(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.account_balance.return_value = [Mock(currency="HKD", total_cash=Decimal("500000"))]
        result = trade_tools.get_account_balance()
        data = json.loads(result)
        assert len(data) == 1
        mock_trade_ctx.account_balance.assert_called_once_with(currency=None)

    def test_get_account_balance_with_currency(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.account_balance.return_value = [Mock(currency="USD")]
        trade_tools.get_account_balance(currency="USD")
        mock_trade_ctx.account_balance.assert_called_once_with(currency="USD")

    def test_get_account_balance_error(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.account_balance.side_effect = MockOpenApiException(code=401, message="Unauthorized")
        result = trade_tools.get_account_balance()
        assert "Error fetching account balance" in result

    def test_get_cash_flow(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.cash_flow.return_value = [Mock(amount=Decimal("1000"))]
        result = trade_tools.get_cash_flow("2024-01-01", "2024-06-30")
        assert "Error" not in result
        call_kwargs = mock_trade_ctx.cash_flow.call_args[1]
        assert call_kwargs["page"] == 1
        assert call_kwargs["size"] == 50

    def test_get_cash_flow_with_params(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.cash_flow.return_value = []
        trade_tools.get_cash_flow("2024-01-01", "2024-06-30", symbol="700.HK", page=2, size=20)
        call_kwargs = mock_trade_ctx.cash_flow.call_args[1]
        assert call_kwargs["symbol"] == "700.HK"
        assert call_kwargs["page"] == 2
        assert call_kwargs["size"] == 20

    def test_get_cash_flow_error(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.cash_flow.side_effect = Exception("Error")
        result = trade_tools.get_cash_flow("2024-01-01", "2024-06-30")
        assert "Error fetching cash flow" in result

    def test_get_stock_positions(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.stock_positions.return_value = Mock(channels=[])
        result = trade_tools.get_stock_positions()
        assert "Error" not in result
        mock_trade_ctx.stock_positions.assert_called_once_with(symbols=None)

    def test_get_stock_positions_with_filter(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.stock_positions.return_value = Mock(channels=[])
        trade_tools.get_stock_positions(symbols="700.HK,AAPL.US")
        mock_trade_ctx.stock_positions.assert_called_once_with(symbols=["700.HK", "AAPL.US"])

    def test_get_stock_positions_error(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.stock_positions.side_effect = MockOpenApiException(code=500, message="Fail")
        result = trade_tools.get_stock_positions()
        assert "Error fetching stock positions" in result

    def test_get_fund_positions(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.fund_positions.return_value = Mock(channels=[])
        result = trade_tools.get_fund_positions()
        assert "Error" not in result
        mock_trade_ctx.fund_positions.assert_called_once_with(symbols=None)

    def test_get_fund_positions_with_filter(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.fund_positions.return_value = Mock(channels=[])
        trade_tools.get_fund_positions(symbols="HK123")
        mock_trade_ctx.fund_positions.assert_called_once_with(symbols=["HK123"])

    def test_get_fund_positions_error(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.fund_positions.side_effect = Exception("Error")
        result = trade_tools.get_fund_positions()
        assert "Error fetching fund positions" in result

    def test_get_margin_ratio(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.margin_ratio.return_value = Mock(
            im_factor=Decimal("0.25"), mm_factor=Decimal("0.20"), fm_factor=Decimal("0.15")
        )
        result = trade_tools.get_margin_ratio("TSLA.US")
        mock_trade_ctx.margin_ratio.assert_called_once_with("TSLA.US")
        assert "Error" not in result

    def test_get_margin_ratio_error(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.margin_ratio.side_effect = MockOpenApiException(code=404, message="Not found")
        result = trade_tools.get_margin_ratio("UNKNOWN.XX")
        assert "Error fetching margin ratio" in result

    def test_estimate_max_purchase_quantity(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.estimate_max_purchase_quantity.return_value = Mock(
            cash_max_qty=Decimal("1000"), margin_max_qty=Decimal("4000")
        )
        result = trade_tools.estimate_max_purchase_quantity(symbol="700.HK", side="Buy", order_type="LO", price="350")
        assert "Error" not in result
        call_kwargs = mock_trade_ctx.estimate_max_purchase_quantity.call_args[1]
        assert call_kwargs["symbol"] == "700.HK"
        assert call_kwargs["side"] == "Buy"
        assert call_kwargs["price"] == Decimal("350")

    def test_estimate_max_purchase_quantity_with_currency(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.estimate_max_purchase_quantity.return_value = Mock()
        trade_tools.estimate_max_purchase_quantity(
            symbol="700.HK", side="Buy", order_type="LO", price="350", currency="HKD"
        )
        call_kwargs = mock_trade_ctx.estimate_max_purchase_quantity.call_args[1]
        assert call_kwargs["currency"] == "HKD"

    def test_estimate_max_purchase_quantity_error(self, trade_tools, mock_trade_ctx):
        mock_trade_ctx.estimate_max_purchase_quantity.side_effect = Exception("Fail")
        result = trade_tools.estimate_max_purchase_quantity(symbol="700.HK", side="Buy", order_type="LO", price="350")
        assert "Error estimating max quantity" in result


# ── Content Tool Tests ──────────────────────────────────────────


class TestContentTools:
    def test_get_news(self, content_tools, mock_content_ctx):
        mock_content_ctx.news.return_value = [Mock(id="1", title="Breaking News", url="https://example.com/news/1")]
        result = content_tools.get_news("700.HK")
        data = json.loads(result)
        assert len(data) == 1
        mock_content_ctx.news.assert_called_once_with("700.HK")

    def test_get_news_empty(self, content_tools, mock_content_ctx):
        mock_content_ctx.news.return_value = []
        result = content_tools.get_news("UNKNOWN.XX")
        data = json.loads(result)
        assert data == []

    def test_get_news_api_error(self, content_tools, mock_content_ctx):
        mock_content_ctx.news.side_effect = MockOpenApiException(code=500, message="Server error")
        result = content_tools.get_news("700.HK")
        assert "Error fetching news" in result
        assert "code=500" in result

    def test_get_news_generic_error(self, content_tools, mock_content_ctx):
        mock_content_ctx.news.side_effect = Exception("Connection refused")
        result = content_tools.get_news("700.HK")
        assert "Error fetching news" in result
        assert "Connection refused" in result

    def test_get_topics(self, content_tools, mock_content_ctx):
        mock_content_ctx.topics.return_value = [Mock(id="1", title="Discussion Thread", likes_count=42)]
        result = content_tools.get_topics("AAPL.US")
        data = json.loads(result)
        assert len(data) == 1
        mock_content_ctx.topics.assert_called_once_with("AAPL.US")

    def test_get_topics_empty(self, content_tools, mock_content_ctx):
        mock_content_ctx.topics.return_value = []
        result = content_tools.get_topics("700.HK")
        data = json.loads(result)
        assert data == []

    def test_get_topics_api_error(self, content_tools, mock_content_ctx):
        mock_content_ctx.topics.side_effect = MockOpenApiException(code=403, message="Forbidden")
        result = content_tools.get_topics("700.HK")
        assert "Error fetching topics" in result
        assert "code=403" in result

    def test_get_topics_generic_error(self, content_tools, mock_content_ctx):
        mock_content_ctx.topics.side_effect = Exception("Timeout")
        result = content_tools.get_topics("700.HK")
        assert "Error fetching topics" in result
        assert "Timeout" in result


# ── Symbol Parsing Tests ────────────────────────────────────────


class TestSymbolParsing:
    def test_comma_separated_symbols(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.quote.return_value = []
        quote_tools.get_quote("700.HK, AAPL.US, TSLA.US")
        mock_quote_ctx.quote.assert_called_once_with(["700.HK", "AAPL.US", "TSLA.US"])

    def test_single_symbol(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.static_info.return_value = []
        quote_tools.get_static_info("700.HK")
        mock_quote_ctx.static_info.assert_called_once_with(["700.HK"])

    def test_symbols_with_spaces(self, quote_tools, mock_quote_ctx):
        mock_quote_ctx.quote.return_value = []
        quote_tools.get_quote("  700.HK ,  AAPL.US  ")
        mock_quote_ctx.quote.assert_called_once_with(["700.HK", "AAPL.US"])
