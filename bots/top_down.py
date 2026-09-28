import requests

BOT_TOKEN = "8826207602:AAEnJMlJOb6lW1QHV4aJ9E8edPacTprTE_Q"
CHAT_ID = "8240862120"
CHANNEL_ID = "@KobbyforexTrade"

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data1 = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, data=data1, timeout=10)
        data2 = {"chat_id": CHANNEL_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, data=data2, timeout=10)
    except:
        pass

from tradingview_ta import TA_Handler, Interval
import pandas as pd

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
    "1D": Interval.INTERVAL_1_DAY,
    "4H": Interval.INTERVAL_4_HOURS,
    "1H": Interval.INTERVAL_1_HOUR,
    "15M": Interval.INTERVAL_15_MINUTES
}

def get_tv_analysis(pair, timeframe):
    """Get live TradingView data for a pair & timeframe"""
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
            "rsi": analysis.indicators["RSI"],
            "ema20": analysis.indicators["EMA20"],
            "ema50": analysis.indicators["EMA50"],
            "summary": analysis.summary["RECOMMENDATION"]
        }
    except Exception as e:
        print(f"TV Error {pair} {timeframe}: {e}")
        return None

def check_liquidity_sweep(data_1h, data_15m):
    """Check if liquidity sweep don happen"""
    # If 15M low sweeps below 1H low then closes back up = Bullish sweep
    # If 15M high sweeps above 1H high then closes back down = Bearish sweep
    try:
        if data_15m["low"] < data_1h["low"] and data_15m["close"] > data_1h["low"]:
            return True, "Bullish Liquidity Sweep - Sell stops grabbed"
        if data_15m["high"] > data_1h["high"] and data_15m["close"] < data_1h["high"]:
            return True, "Bearish Liquidity Sweep - Buy stops grabbed"
        return False, "No Sweep Yet"
    except:
        return False, "No Data"

def check_fibonacci_zone(swing_high, swing_low, current_price, bias):
    """Check if price dey inside 50%-79% Fib discount/premium"""
    try:
        fib_range = swing_high - swing_low
        fib_50 = swing_high - fib_range * 0.5 if bias == "BUY" else swing_low + fib_range * 0.5
        fib_79 = swing_high - fib_range * 0.79 if bias == "BUY" else swing_low + fib_range * 0.79

        if bias == "BUY":
            in_zone = fib_79 <= current_price <= fib_50
        else:
            in_zone = fib_50 <= current_price <= fib_79

        return in_zone, f"Fib 50%-79% Zone: {fib_50:.5f} - {fib_79:.5f}"
    except:
        return False, "Fib Error"

def analyze_top_down(pair):
    """
    FULL BOT 1 - TradingView Technical Confluence
    Top Down 1D-4H-1H-15M + SMC + Liquidity + Fib + Supply/Demand + POI
    """
    # Step 1: Get all timeframes LIVE from TradingView
    d1 = get_tv_analysis(pair, "1D")
    h4 = get_tv_analysis(pair, "4H")
    h1 = get_tv_analysis(pair, "1H")
    m15 = get_tv_analysis(pair, "15M")

    if not all([d1, h4, h1, m15]):
        return {"pair": pair, "setup": False, "reason": "TradingView data incomplete"}

    # Step 2: Top Down Bias
    # 1D trend
    if d1["close"] > d1["ema50"] and d1["summary"] in ["BUY", "STRONG_BUY"]:
        bias_1d = "BUY"
    elif d1["close"] < d1["ema50"] and d1["summary"] in ["SELL", "STRONG_SELL"]:
        bias_1d = "SELL"
    else:
        return {"pair": pair, "setup": False, "reason": f"1D No clear trend for {pair}"}

    # 4H must align with 1D (SMC BOS)
    h4_bias = "BUY" if h4["close"] > h4["ema20"] else "SELL"
    if h4_bias!= bias_1d:
        return {"pair": pair, "setup": False, "reason": f"4H {h4_bias} no align with 1D {bias_1d} - Wait for BOS alignment"}

    # Step 3: Liquidity Sweep Check
    sweep_ok, sweep_msg = check_liquidity_sweep(h1, m15)
    if not sweep_ok:
        return {"pair": pair, "setup": False, "reason": sweep_msg, "bias": bias_1d}

    # Step 4: Supply/Demand + POI (Point of Interest)
    # Use 1H high/low as Supply/Demand, 15M close as entry check
    if bias_1d == "BUY":
        demand_zone = h1["low"]
        supply_zone = h1["high"]
        # Check if price near demand (POI)
        poi = m15["close"] <= h1["low"] * 1.001 # Within 0.1% of demand
    else:
        demand_zone = h1["low"]
        supply_zone = h1["high"]
        poi = m15["close"] >= h1["high"] * 0.999

    # Step 5: Fibonacci 50-79% Check
    fib_ok, fib_msg = check_fibonacci_zone(h1["high"], h1["low"], m15["close"], bias_1d)

    # Step 6: FINAL CONFLUENCE
    if sweep_ok and poi and fib_ok:
        return {
            "pair": pair,
            "setup": True,
            "bias": bias_1d,
            "source": "TECHNICAL",
            "entry_price": m15["close"],
            "stop_loss": h1["low"] if bias_1d == "BUY" else h1["high"],
            "poi": f"Supply: {supply_zone} | Demand: {demand_zone}",
            "confluence": f"✅ 1D {bias_1d} | 4H BOS aligned | {sweep_msg} | {fib_msg} | POI inside Demand/Supply",
            "timeframes": {"1D": d1, "4H": h4, "1H": h1, "15M": m15}
        }
    else:
        return {
            "pair": pair,
            "setup": False,
            "bias": bias_1d,
            "reason": f"Sweep:{sweep_ok} POI:{poi} Fib:{fib_ok} - {fib_msg} - {sweep_msg}",
            "entry_price": m15["close"]
        }

if __name__ == "__main__":
    print(analyze_top_down("GBPUSD"))
