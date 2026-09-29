import time, random
from tradingview_ta import TA_Handler, Interval

PAIRS_MAP = {
    "XAUUSD": {"symbol": "XAUUSD", "exchange": "OANDA", "screener": "forex"}
}
# Alternative if OANDA still 429: use FX_IDC
BACKUP_MAP = {
    "XAUUSD": {"symbol": "XAUUSD", "exchange": "FX_IDC", "screener": "forex"}
}

INTERVAL_MAP = {
    "4H": Interval.INTERVAL_4_HOURS,
    "1H": Interval.INTERVAL_1_HOUR,
    "15M": Interval.INTERVAL_15_MINUTES
}

# global last success cache
CACHE = {}

def get_tv(pair, tf):
    global CACHE
    key = f"{pair}_{tf}"

    for attempt in range(3):
        try:
            # Anti-block: random 5-8 sec delay
            delay = random.uniform(5, 8)
            print(f"TV Wait {delay:.1f}s for {pair} {tf}...", flush=True)
            time.sleep(delay)

            c = PAIRS_MAP.get(pair)
            h = TA_Handler(symbol=c["symbol"], exchange=c["exchange"], screener=c["screener"], interval=INTERVAL_MAP[tf])
            a = h.get_analysis()
            data = {"close": a.indicators["close"], "open": a.indicators["open"], "high": a.indicators["high"], "low": a.indicators["low"]}
            CACHE[key] = data
            print(f"TV OK {pair} {tf}: {data['close']}", flush=True)
            return data

        except Exception as e:
            err = str(e)
            print(f"TV {pair} {tf} attempt {attempt} fail: {err}", flush=True)

            # If 429, wait 70 sec + try backup exchange
            if "429" in err:
                print("TV 429 DETECTED - Sleeping 70s to cool down", flush=True)
                time.sleep(70)
                # try backup exchange on last attempt
                if attempt == 1:
                    try:
                        print(f"Trying BACKUP exchange for {pair}", flush=True)
                        c = BACKUP_MAP.get(pair)
                        h = TA_Handler(symbol=c["symbol"], exchange=c["exchange"], screener=c["screener"], interval=INTERVAL_MAP[tf])
                        a = h.get_analysis()
                        data = {"close": a.indicators["close"], "open": a.indicators["open"], "high": a.indicators["high"], "low": a.indicators["low"]}
                        CACHE[key] = data
                        return data
                    except Exception as e2:
                        print(f"Backup also fail: {e2}", flush=True)
            else:
                time.sleep(10)

    # If all fail, return cached data if exists
    if key in CACHE:
        print(f"Using CACHED data for {pair} {tf}", flush=True)
        return CACHE[key]
    return None

def analyze_top_down(pair):
    h4 = get_tv(pair, "4H")
    h1 = get_tv(pair, "1H")
    m15 = get_tv(pair, "15M")

    if not all([h4, h1, m15]):
        return {"setup": False, "reason": "TV data incomplete - 429 cooldown"}

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
