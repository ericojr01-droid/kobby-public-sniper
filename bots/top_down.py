import time, random
from tradingview_ta import TA_Handler, Interval

# Try multiple exchanges - first that works wins
EXCHANGES_TO_TRY = [
    {"symbol": "XAUUSD", "exchange": "OANDA", "screener": "forex"},
    {"symbol": "XAUUSD", "exchange": "FX", "screener": "forex"},
    {"symbol": "XAUUSD", "exchange": "FOREXCOM", "screener": "forex"},
    {"symbol": "XAUUSD", "exchange": "FX_IDC", "screener": "forex"},
    {"symbol": "GOLD", "exchange": "CAPITALCOM", "screener": "cfd"},
    {"symbol": "GOLD", "exchange": "TVC", "screener": "cfd"},
    {"symbol": "XAUUSD", "exchange": "CAPITALCOM", "screener": "forex"},
]

INTERVAL_MAP = {
    "4H": Interval.INTERVAL_4_HOURS,
    "1H": Interval.INTERVAL_1_HOUR,
    "15M": Interval.INTERVAL_15_MINUTES
}
CACHE = {}

def get_tv(pair, tf):
    key = f"{pair}_{tf}"
    for attempt in range(len(EXCHANGES_TO_TRY)):
        cfg = EXCHANGES_TO_TRY[attempt]
        try:
            delay = random.uniform(3, 5)
            print(f"TV Try {cfg['exchange']}:{cfg['symbol']} {tf} (attempt {attempt})...", flush=True)
            time.sleep(delay)
            h = TA_Handler(symbol=cfg["symbol"], exchange=cfg["exchange"], screener=cfg["screener"], interval=INTERVAL_MAP[tf])
            a = h.get_analysis()
            data = {"close": a.indicators["close"], "open": a.indicators["open"], "high": a.indicators["high"], "low": a.indicators["low"]}
            CACHE[key] = data
            print(f"TV SUCCESS {cfg['exchange']} {tf}: {data['close']}", flush=True)
            return data
        except Exception as e:
            print(f"TV {cfg['exchange']} {tf} fail: {e}", flush=True)
            if "429" in str(e):
                print("429 - sleep 60s", flush=True)
                time.sleep(60)
            continue
    if key in CACHE:
        print(f"Using CACHE {pair} {tf}", flush=True)
        return CACHE[key]
    return None

def analyze_top_down(pair):
    h4 = get_tv(pair, "4H"); h1 = get_tv(pair, "1H"); m15 = get_tv(pair, "15M")
    if not all([h4,h1,m15]): return {"setup": False, "reason": "TV all exchanges fail - retry next scan"}
    bias = "BUY" if h4["close"] > h4["open"] else "SELL"
    if bias == "BUY":
        sweep = m15["low"] < h1["low"] and m15["close"] > h1["low"]
        sweep_msg = f"SSL Sweep {h1['low']:.2f}" if sweep else "No SSL Sweep"
        sl_price = h1["low"]
    else:
        sweep = m15["high"] > h1["high"] and m15["close"] < h1["high"]
        sweep_msg = f"BSL Sweep {h1['high']:.2f}" if sweep else "No BSL Sweep"
        sl_price = h1["high"]
    if not sweep: return {"pair": pair, "setup": False, "bias": bias, "reason": sweep_msg}
    bos = (m15["close"] > h1["high"] or h1["close"] > h4["high"]) if bias=="BUY" else (m15["close"] < h1["low"] or h1["close"] < h4["low"])
    if not bos: return {"pair": pair, "setup": False, "bias": bias, "reason": "No BOS/CHoCH"}
    swing_h = max(h4["high"], h1["high"]); swing_l = min(h4["low"], h1["low"]); rng = swing_h - swing_l
    if bias=="BUY":
        f50 = swing_h - rng*0.5; f79 = swing_h - rng*0.79; fib_ok = f79 <= m15["close"] <= f50
    else:
        f50 = swing_l + rng*0.5; f79 = swing_l + rng*0.79; fib_ok = f50 <= m15["close"] <= f79
    if not fib_ok: return {"pair": pair, "setup": False, "bias": bias, "reason": "Not in Fib 50-79%"}
    ob = (m15["close"] > m15["open"]) if bias=="BUY" else (m15["close"] < m15["open"])
    if not ob: return {"pair": pair, "setup": False, "bias": bias, "reason": "No OB"}
    return {"pair": pair, "setup": True, "bias": bias, "strength": "SNIPER 🔥🔥🔥", "source": "PURE-SMC-4H-1H-15M", "entry_price": m15["close"], "stop_loss": sl_price, "confluence": f"{sweep_msg} | BOS ✅ | Fib 50-79% ✅ | OB ✅ | 15M Confirm ✅"}
