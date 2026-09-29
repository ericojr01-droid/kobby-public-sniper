import requests
import os
import time
from tradingview_ta import TA_Handler, Interval

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data1 = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, data=data1, timeout=10)
        data2 = {"chat_id": CHANNEL_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, data=data2, timeout=10)
    except:
        pass

PAIRS_MAP = {
    "GBPUSD": {"symbol": "GBPUSD", "exchange": "FX", "screener": "forex"},
    "GBPJPY": {"symbol": "GBPJPY", "exchange": "FX", "screener": "forex"},
    "XAUUSD": {"symbol": "XAUUSD", "exchange": "OANDA", "screener": "forex"},
    "AUDCAD": {"symbol": "AUDCAD", "exchange": "FX", "screener": "forex"},
    "EURUSD": {"symbol": "EURUSD", "exchange": "FX", "screener": "forex"},
    "AUDUSD": {"symbol": "AUDUSD", "exchange": "FX", "screener": "forex"},
    "USDJPY": {"symbol": "USDJPY", "exchange": "FX", "screener": "forex"},
    "BTCUSD": {"symbol": "BTCUSD", "exchange": "BINANCE", "screener": "crypto"},
    "NAS100": {"symbol": "NAS100", "exchange": "NASDAQ", "screener": "america"},
    "SPX500": {"symbol": "SPX500", "exchange": "FOREXCOM", "screener": "forex"},
}

INTERVAL_MAP = {
    "4H": Interval.INTERVAL_4_HOURS,
    "1H": Interval.INTERVAL_1_HOUR,
    "15M": Interval.INTERVAL_15_MINUTES
}

def get_tv_analysis(pair, timeframe):
    config = PAIRS_MAP.get(pair)
    try:
        handler = TA_Handler(
            symbol=config["symbol"],
            exchange=config["exchange"],
            screener=config["screener"],
            interval=INTERVAL_MAP[timeframe]
        )
        analysis = handler.get_analysis()
        return {
            "close": analysis.indicators["close"],
            "open": analysis.indicators["open"],
            "high": analysis.indicators["high"],
            "low": analysis.indicators["low"],
        }
    except Exception as e:
        print(f"TV Error {pair} {timeframe}: {e}")
        return None

def check_liquidity_sweep(data_1h, data_15m):
    try:
        if data_15m["low"] < data_1h["low"] and data_15m["close"] > data_1h["low"]:
            return True, f"SSL Sweep below {data_1h['low']:.5f} ✅"
        if data_15m["high"] > data_1h["high"] and data_15m["close"] < data_1h["high"]:
            return True, f"BSL Sweep above {data_1h['high']:.5f} ✅"
        return False, "No Sweep ❌"
    except:
        return False, "No Data"

def check_bos_choch(h4, h1, m15, bias):
    try:
        if bias == "BUY":
            if m15["close"] > h1["high"] or h1["close"] > h4["high"]:
                if h1["close"] > h4["high"]:
                    return True, f"BOS Bullish Broke 4H {h4['high']:.5f} ✅"
                else:
                    return True, f"CHoCH Bullish Broke 1H {h1['high']:.5f} ✅"
        else:
            if m15["close"] < h1["low"] or h1["close"] < h4["low"]:
                if h1["close"] < h4["low"]:
                    return True, f"BOS Bearish Broke 4H {h4['low']:.5f} ✅"
                else:
                    return True, f"CHoCH Bearish Broke 1H {h1['low']:.5f} ✅"
        return False, "No BOS/CHoCH ❌"
    except:
        return False, "BOS Error"

def check_fibonacci_zone(swing_high, swing_low, current_price, bias):
    try:
        fib_range = swing_high - swing_low
        if bias == "BUY":
            fib_50 = swing_high - fib_range * 0.5
            fib_79 = swing_high - fib_range * 0.79
            in_zone = fib_79 <= current_price <= fib_50
        else:
            fib_50 = swing_low + fib_range * 0.5
            fib_79 = swing_low + fib_range * 0.79
            in_zone = fib_50 <= current_price <= fib_79
        return in_zone, f"Fib 50-79% {fib_50:.5f}-{fib_79:.5f} {'INSIDE ✅' if in_zone else 'OUTSIDE'}"
    except:
        return False, "Fib Error"

def check_order_block(data_15m, bias):
    try:
        if bias == "BUY" and data_15m["close"] > data_15m["open"]:
            return True, f"OB Demand {data_15m['low']:.5f} ✅"
        if bias == "SELL" and data_15m["close"] < data_15m["open"]:
            return True, f"OB Supply {data_15m['high']:.5f} ✅"
        return False, "No OB"
    except:
        return False, "OB Error"

def check_fvg(data_1h, data_15m, bias):
    try:
        range_1h = data_1h["high"] - data_1h["low"]
        if range_1h == 0: return False, "No range"
        if bias == "BUY" and (data_1h["low"] - data_15m["low"]) > (range_1h * 0.15):
            return True, "FVG Bullish ✅"
        if bias == "SELL" and (data_15m["high"] - data_1h["high"]) > (range_1h * 0.15):
            return True, "FVG Bearish ✅"
        return False, "No FVG"
    except:
        return False, "FVG Error"

def check_15m_confirmation(data_15m, bias):
    try:
        if bias == "BUY":
            return data_15m["close"] > data_15m["open"], "15M Bullish Confirm ✅"
        else:
            return data_15m["close"] < data_15m["open"], "15M Bearish Confirm ✅"
    except:
        return False, "No 15M Data"

def analyze_top_down(pair):
    h4 = get_tv_analysis(pair, "4H")
    h1 = get_tv_analysis(pair, "1H")
    m15 = get_tv_analysis(pair, "15M")
    if not all([h4, h1, m15]):
        return {"pair": pair, "setup": False, "reason": "TV data incomplete"}

    # 4H Bias pure PA
    if h4["close"] > h1["high"]:
        bias_4h = "BUY"
    elif h4["close"] < h1["low"]:
        bias_4h = "SELL"
    else:
        bias_4h = "BUY" if h4["close"] > h4["open"] else "SELL"

    # POI
    if bias_4h == "BUY":
        poi = m15["close"] <= h1["low"] * 1.003
        poi_msg = f"1H Demand POI {h1['low']:.5f}"
    else:
        poi = m15["close"] >= h1["high"] * 0.997
        poi_msg = f"1H Supply POI {h1['high']:.5f}"
    if not poi:
        return {"pair": pair, "setup": False, "bias": bias_4h, "reason": f"Not at POI {m15['close']:.5f}"}

    sweep_ok, sweep_msg = check_liquidity_sweep(h1, m15)
    if not sweep_ok:
        return {"pair": pair, "setup": False, "bias": bias_4h, "reason": sweep_msg}

    bos_ok, bos_msg = check_bos_choch(h4, h1, m15, bias_4h)
    if not bos_ok:
        return {"pair": pair, "setup": False, "bias": bias_4h, "reason": bos_msg}

    ob_ok, ob_msg = check_order_block(m15, bias_4h)
    fvg_ok, fvg_msg = check_fvg(h1, m15, bias_4h)
    if not (ob_ok or fvg_ok):
        return {"pair": pair, "setup": False, "bias": bias_4h, "reason": "No OB/FVG"}

    confirm_ok, confirm_msg = check_15m_confirmation(m15, bias_4h)
    if not confirm_ok:
        return {"pair": pair, "setup": False, "bias": bias_4h, "reason": "No 15M confirm"}

    fib_ok, fib_msg = check_fibonacci_zone(h1["high"], h1["low"], m15["close"], bias_4h)

    score = 0
    if fib_ok: score += 1
    if ob_ok and fvg_ok: score += 1
    if "CHoCH" in bos_msg: score += 1

    if score >= 3:
        strength = "SNIPER 🔥🔥🔥"
    elif score == 2:
        strength = "STRONG ✅✅"
    elif score == 1:
        strength = "STRONG ✅"
    else:
        strength = "SETUP ✅"

    return {
        "pair": pair, "setup": True, "bias": bias_4h, "strength": strength,
        "source": "PURE-SMC-4H-1H-15M",
        "entry_price": m15["close"],
        "stop_loss": h1["low"] if bias_4h == "BUY" else h1["high"],
        "confluence": f"{strength} | {poi_msg} | {sweep_msg} | {bos_msg} | {ob_msg if ob_ok else ''} {fvg_msg if fvg_ok else ''} | {fib_msg} | {confirm_msg}",
    }

def scan_all_pairs():
    print("=== Scanning all 10 pairs - Pure SMC ===")
    for pair in PAIRS_MAP.keys():
        result = analyze_top_down(pair)
        if result["setup"]:
            msg = f"""
🔥 <b>{result['pair']} {result['bias']} - {result['strength']}</b>
Pure SMC 4H-1H-15M
Entry: {result['entry_price']:.5f}
SL: {result['stop_loss']:.5f}
{result['confluence']}
"""
            send_telegram(msg)
            print(f"✅ Signal {pair}")
        else:
            print(f"❌ {pair}: {result.get('reason','No setup')}")
        time.sleep(2) # avoid TradingView block

if __name__ == "__main__":
    scan_all_pairs()
