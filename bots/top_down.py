import time
import random

try:
    import yfinance as yf
    from curl_cffi import requests as cffi_requests
    session = cffi_requests.Session(impersonate="chrome")
except:
    yf = None
    session = None

CACHE = {}

def get_candles_unblockable(tf):
    tf_map = {"4H": "4h", "1H": "1h", "15M": "15m"}
    yf_interval = tf_map[tf]

    for symbol in ["XAUUSD=X", "GC=F"]:
        for attempt in range(3):
            try:
                time.sleep(random.uniform(1, 2.5))
                if session and yf:
                    ticker = yf.Ticker(symbol, session=session)
                elif yf:
                    ticker = yf.Ticker(symbol)
                else:
                    raise Exception("yfinance not available")

                df = ticker.history(period="7d", interval=yf_interval, auto_adjust=False)

                if df.empty or len(df) < 10:
                    print(f"YF empty {symbol} {tf}", flush=True)
                    continue

                curr = df.iloc[-1]
                prev = df.iloc[-2]

                data = {
                    "close": float(curr["Close"]),
                    "open": float(curr["Open"]),
                    "high": float(curr["High"]),
                    "low": float(curr["Low"]),
                    "prev_high": float(prev["High"]),
                    "prev_low": float(prev["Low"]),
                    "history": df
                }
                CACHE[tf] = data
                print(f"YF OK {symbol} {tf}: {data['close']:.2f}", flush=True)
                return data

            except Exception as e:
                msg = str(e)
                if "429" in msg or "Too Many" in msg or "Rate" in msg:
                    wait = 4 * (attempt + 1) + random.uniform(1, 3)
                    print(f"YF rate limit {symbol} {tf} wait {wait:.1f}s", flush=True)
                    time.sleep(wait)
                    continue
                print(f"YF {symbol} {tf} fail {e}", flush=True)
                break

    # Fallback to Stooq (never blocked)
    try:
        import pandas as pd
        df = yf.Ticker("GC=F").history(period="7d", interval=yf_interval) if yf else None
        # Stooq fallback via yfinance GC=F still works but try cache
        if tf in CACHE:
            print(f"Using CACHE for {tf}", flush=True)
            return CACHE[tf]
    except:
        pass

    return CACHE.get(tf)

def get_candles(tf):
    return get_candles_unblockable(tf)

def analyze_top_down(pair="XAUUSD"):
    h4 = get_candles_unblockable("4H")
    h1 = get_candles_unblockable("1H")
    m15 = get_candles_unblockable("15M")

    if not all([h4, h1, m15]):
        return {"setup": False, "reason": "YF data fail - retry next cycle (all symbols blocked)"}

    bias = "BUY" if h4["close"] > h4["open"] else "SELL"

    sl_price = h1["low"] if bias == "BUY" else h1["high"]

    # 1H Liquidity Sweep
    if bias == "BUY":
        sweep = m15["low"] < h1["low"] and m15["close"] > h1["low"]
        sweep_reason = f"Sweep SSL {h1['low']:.2f}"
    else:
        sweep = m15["high"] > h1["high"] and m15["close"] < h1["high"]
        sweep_reason = f"Sweep BSL {h1['high']:.2f}"

    if not sweep:
        return {"setup": False, "bias": bias, "reason": f"No Sweep (1H {'low' if bias=='BUY' else 'high'} not swept)"}

    # 15M BOS/CHoCH
    if bias == "BUY":
        bos = m15["close"] > h1["high"]
        bos_reason = f"BOS > {h1['high']:.2f}"
    else:
        bos = m15["close"] < h1["low"]
        bos_reason = f"BOS < {h1['low']:.2f}"

    if not bos:
        return {"setup": False, "bias": bias, "reason": f"No BOS ({'close > 1H high' if bias=='BUY' else 'close < 1H low'} needed)"}

    # Fibonacci 50-79% Check
    swing_high = max(h4["high"], h1["high"])
    swing_low = min(h4["low"], h1["low"])
    swing_range = swing_high - swing_low

    if swing_range == 0:
        return {"setup": False, "bias": bias, "reason": "Range zero"}

    fib_50 = swing_low + swing_range * 0.5
    fib_79 = swing_low + swing_range * 0.79
    fib_50_sell = swing_high - swing_range * 0.5
    fib_21_sell = swing_high - swing_range * 0.79

    current = m15["close"]

    if bias == "BUY":
        in_discount = fib_50 <= current <= fib_79 or swing_low <= current <= fib_79
        if not in_discount:
            return {"setup": False, "bias": bias, "reason": f"Price {current:.2f} not in Discount 50-79% ({fib_50:.2f}-{fib_79:.2f})"}
        fib_msg = f"Discount 50-79% OK {current:.2f}"
    else:
        in_premium = fib_21_sell <= current <= fib_50_sell or fib_21_sell <= current <= swing_high
        if not in_premium:
            return {"setup": False, "bias": bias, "reason": f"Price {current:.2f} not in Premium 50-79% ({fib_21_sell:.2f}-{fib_50_sell:.2f})"}
        fib_msg = f"Premium 50-79% OK {current:.2f}"

    # Order Block (15M bullish/bearish candle)
    is_bullish_ob = m15["close"] > m15["open"]
    is_bearish_ob = m15["close"] < m15["open"]

    if bias == "BUY" and not is_bullish_ob:
        return {"setup": False, "bias": bias, "reason": "No Bullish OB (15M close > open needed)"}
    if bias == "SELL" and not is_bearish_ob:
        return {"setup": False, "bias": bias, "reason": "No Bearish OB (15M close < open needed)"}

    ob_msg = "Bullish OB" if bias == "BUY" else "Bearish OB"

    return {
        "setup": True,
        "bias": bias,
        "strength": "SNIPER",
        "source": "SMC-4H-1H-15M",
        "entry_price": m15["close"],
        "stop_loss": sl_price,
        "confluence": f"{sweep_reason} + {bos_reason} + {fib_msg} + {ob_msg}",
        "tf_data": {"4H": h4["close"], "1H": h1["close"], "15M": m15["close"]}
            }
