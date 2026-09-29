import time
from tradingview_ta import TA_Handler, Interval

PAIRS_MAP = {
    "XAUUSD": {"symbol": "XAUUSD", "exchange": "OANDA", "screener": "forex"}
}
INTERVAL_MAP = {
    "4H": Interval.INTERVAL_4_HOURS,
    "1H": Interval.INTERVAL_1_HOUR,
    "15M": Interval.INTERVAL_15_MINUTES
}

def get_tv(pair, tf):
    c = PAIRS_MAP[pair]
    for attempt in range(2):
        try:
            time.sleep(2.5)
            h = TA_Handler(symbol=c["symbol"], exchange=c["exchange"], screener=c["screener"], interval=INTERVAL_MAP[tf])
            a = h.get_analysis()
            return {
                "close": a.indicators["close"],
                "open": a.indicators["open"],
                "high": a.indicators["high"],
                "low": a.indicators["low"]
            }
        except Exception as e:
            print(f"TV {pair} {tf} attempt {attempt} fail: {e}", flush=True)
            time.sleep(4)
    return None

def analyze_top_down(pair):
    h4 = get_tv(pair, "4H")
    h1 = get_tv(pair, "1H")
    m15 = get_tv(pair, "15M")
    if not all([h4, h1, m15]):
        return {"setup": False, "reason": "TV data incomplete"}

    bias = "BUY" if h4["close"] > h4["open"] else "SELL"

    if bias == "BUY":
        sweep = m15["low"] < h1["low"] and m15["close"] > h1["low"]
        sweep_msg = f"SSL Sweep {h1['low']:.2f}" if sweep else "No SSL Sweep"
        sl_price = h1["low"]
    else:
        sweep = m15["high"] > h1["high"] and m15["close"] < h1["high"]
        sweep_msg = f"BSL Sweep {h1['high']:.2f}" if sweep else "No BSL Sweep"
        sl_price = h1["high"]

    if not sweep:
        return {"pair": pair, "setup": False, "bias": bias, "reason": sweep_msg}

    if bias == "BUY":
        bos = m15["close"] > h1["high"] or h1["close"] > h4["high"]
    else:
        bos = m15["close"] < h1["low"] or h1["close"] < h4["low"]

    if not bos:
        return {"pair": pair, "setup": False, "bias": bias, "reason": "No BOS/CHoCH"}

    swing_h = max(h4["high"], h1["high"])
    swing_l = min(h4["low"], h1["low"])
    fib_range = swing_h - swing_l

    if bias == "BUY":
        f50 = swing_h - fib_range * 0.5
        f79 = swing_h - fib_range * 0.79
        fib_ok = f79 <= m15["close"] <= f50
    else:
        f50 = swing_l + fib_range * 0.5
        f79 = swing_l + fib_range * 0.79
        fib_ok = f50 <= m15["close"] <= f79

    if not fib_ok:
        return {"pair": pair, "setup": False, "bias": bias, "reason": "Not in Fib 50-79%"}

    if bias == "BUY":
        ob = m15["close"] > m15["open"]
    else:
        ob = m15["close"] < m15["open"]

    if not ob:
        return {"pair": pair, "setup": False, "bias": bias, "reason": "No OB"}

    if bias == "BUY":
        confirm = m15["close"] > m15["open"]
    else:
        confirm = m15["close"] < m15["open"]

    if not confirm:
        return {"pair": pair, "setup": False, "bias": bias, "reason": "No 15M Confirm"}

    return {
        "pair": pair,
        "setup": True,
        "bias": bias,
        "strength": "SNIPER 🔥🔥🔥",
        "source": "PURE-SMC-4H-1H-15M",
        "entry_price": m15["close"],
        "stop_loss": sl_price,
        "confluence": f"{sweep_msg} | BOS ✅ | Fib 50-79% ✅ | OB ✅ | 15M Confirm ✅"
}
