import time
import random
from tradingview_ta import TA_Handler, Interval

EXCHANGES = [
    {"symbol": "GOLD", "exchange": "CAPITALCOM", "screener": "cfd"},
    {"symbol": "GOLD", "exchange": "TVC", "screener": "cfd"},
    {"symbol": "XAUUSD", "exchange": "FX_IDC", "screener": "forex"},
]

INTERVAL_MAP = {
    "4H": Interval.INTERVAL_4_HOURS,
    "1H": Interval.INTERVAL_1_HOUR,
    "15M": Interval.INTERVAL_15_MINUTES,
}

CACHE = {}

def get_tv(tf):
    for cfg in EXCHANGES:
        try:
            time.sleep(random.uniform(2, 4))
            handler = TA_Handler(
                symbol=cfg["symbol"],
                exchange=cfg["exchange"],
                screener=cfg["screener"],
                interval=INTERVAL_MAP[tf],
            )
            analysis = handler.get_analysis()
            data = {
                "close": analysis.indicators["close"],
                "open": analysis.indicators["open"],
                "high": analysis.indicators["high"],
                "low": analysis.indicators["low"],
            }
            CACHE[tf] = data
            print(f"TV OK {cfg['exchange']} {tf} {data['close']}", flush=True)
            return data
        except Exception as e:
            print(f"TV {cfg['exchange']} {tf} fail {e}", flush=True)
            continue
    return CACHE.get(tf)

def analyze_top_down(pair):
    h4 = get_tv("4H")
    h1 = get_tv("1H")
    m15 = get_tv("15M")
    if not all([h4, h1, m15]):
        return {"setup": False, "reason": "TV data fail"}
    bias = "BUY" if h4["close"] > h4["open"] else "SELL"
    sl_price = h1["low"] if bias == "BUY" else h1["high"]
    if bias == "BUY":
        sweep = m15["low"] < h1["low"] and m15["close"] > h1["low"]
    else:
        sweep = m15["high"] > h1["high"] and m15["close"] < h1["high"]
    if not sweep:
        return {"setup": False, "bias": bias, "reason": "No Sweep"}
    if bias == "BUY":
        bos = m15["close"] > h1["high"]
    else:
        bos = m15["close"] < h1["low"]
    if not bos:
        return {"setup": False, "bias": bias, "reason": "No BOS"}
    return {
        "setup": True,
        "bias": bias,
        "strength": "SNIPER",
        "source": "PURE-SMC-XAU",
        "entry_price": m15["close"],
        "stop_loss": sl_price,
        "confluence": "Sweep BOS OK",
}
