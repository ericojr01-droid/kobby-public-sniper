from .top_down import analyze_top_down, get_candles, get_candles_unblockable
from .fundamental import analyze_fundamental, is_news_block_active, fetch_forexfactory_news, get_dxy_tnx_bias
from .entry_risk import generate_entry, get_entry_levels, get_entry, calc_lot_size, calc_lot, get_pip
from .market_status import (
    is_trading_allowed,
    check_session_status,
    is_forex_market_open,
    should_send_session_alert,
    should_send_market_open_close_alert,
    get_session_status_message
)

calculate_lot_size = calc_lot_size
get_market_status_alert = check_session_status
check_all_pairs_status = check_session_status

__all__ = [
    "analyze_top_down",
    "get_candles",
    "get_candles_unblockable",
    "analyze_fundamental",
    "is_news_block_active",
    "fetch_forexfactory_news",
    "get_dxy_tnx_bias",
    "generate_entry",
    "get_entry_levels",
    "get_entry",
    "calc_lot_size",
    "calculate_lot_size",
    "calc_lot",
    "get_pip",
    "is_trading_allowed",
    "check_session_status",
    "is_forex_market_open",
    "should_send_session_alert",
    "should_send_market_open_close_alert",
    "get_session_status_message",
    "get_market_status_alert",
    "check_all_pairs_status",
]
