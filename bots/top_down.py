import yfinance as yf
import time
import random
CACHE = {}

def get_candles(tf):
    tf_map = {"4H": "4h", "1H": "1h", "15M": "15m"}
    for symbol in ["XAUUSD=X", "GC=F"]:
        for attempt in range(3):
            try:
                time.sleep(random.uniform(3, 6)) # delay to avoid Yahoo 429
                ticker = yf.Ticker(symbol)
                df = ticker.history(period="5d", interval=tf_map[tf])
                if df.empty:
                    continue
                curr = df.iloc[-1]
                data = {"close": float(curr["Close"]), "open": float(curr["Open"]), "high": float(curr["High"]), "low": float(curr["Low"])}
                CACHE[tf] = data
                print(f"YF OK {symbol} {tf}: {data['close']:.2f}", flush=True)
                return data
            except Exception as e:
                msg = str(e)
                if "Too Many Requests" in msg or "Rate limited" in msg:
                    print(f"YF rate limited {symbol} {tf}, waiting {5*attempt+5}s...", flush=True)
                    time.sleep(5*attempt+5)
                    continue
                print(f"YF {symbol} {tf} fail {e}", flush=True)
                break
    return CACHE.get(tf)

def analyze_top_down(pair):
    h4 = get_candles("4H")
    h1 = get_candles("1H")
    m15 = get_candles("15M")
    if not all([h4, h1, m15]):
        return {"setup": False, "reason": "YF data fail - retry next cycle"}
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
    return {"setup": True, "bias": bias, "strength": "SNIPER", "source": "XAUUSD SPOT", "entry_price": m15["close"], "stop_loss": sl_price, "confluence": "Sweep BOS OK"}
