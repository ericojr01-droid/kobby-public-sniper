import yfinance as yf
import time
import os
import requests
from datetime import datetime
from flask import Flask
import threading

SYMBOL = "BTC-USD"
RR1, RR2, RR3 = 2, 3, 5

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

app = Flask(__name__)
@app.route('/')
def home():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S Ghana")
    return f"kobby_btcbot LIVE - SMC {now}"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def get_smc_setup():
    # Top Down: 4H, 1H, 15M - no indicators
    df4h = yf.download(SYMBOL, period="20d", interval="4h", auto_adjust=True, progress=False)
    df1h = yf.download(SYMBOL, period="10d", interval="60m", auto_adjust=True, progress=False)
    df15 = yf.download(SYMBOL, period="5d", interval="15m", auto_adjust=True, progress=False)

    if len(df4h) < 30 or len(df1h) < 30 or len(df15) < 30:
        return None

    # 1. 4H TREND - Swing Highs/Lows
    high_4h = float(df4h['High'].iloc[-20:-1].max())
    low_4h = float(df4h['Low'].iloc[-20:-1].min())
    close_4h = float(df4h['Close'].iloc[-1])
    trend_4h = "BULLISH" if close_4h > (high_4h + low_4h)/2 else "BEARISH"

    # 2. 1H - MAIN ANALYSIS (Mandatory)
    # Swing levels
    swing_high_1h = float(df1h['High'].iloc[-30:-5].max())
    swing_low_1h = float(df1h['Low'].iloc[-30:-5].min())
    
    # Liquidity Sweep MUST - price swept previous high/low then closed back
    # Buy: swept low, Sell: swept high
    last_5_high = float(df1h['High'].iloc[-5:].max())
    last_5_low = float(df1h['Low'].iloc[-5:].min())
    close_1h = float(df1h['Close'].iloc[-1])
    
    swept_low = last_5_low < swing_low_1h and close_1h > swing_low_1h
    swept_high = last_5_high > swing_high_1h and close_1h < swing_high_1h

    # BOS MUST - Break of Structure
    recent_high_1h = float(df1h['High'].iloc[-15:-1].max())
    recent_low_1h = float(df1h['Low'].iloc[-15:-1].min())
    
    bos_bull = close_1h > recent_high_1h
    bos_bear = close_1h < recent_low_1h

    # OB / FVG / Supply Demand
    # OB: last bearish candle before bullish move
    bullish_ob = float(df1h['Low'].iloc[-3]) if df1h['Close'].iloc[-2] > df1h['Open'].iloc[-2] else None
    bearish_ob = float(df1h['High'].iloc[-3]) if df1h['Close'].iloc[-2] < df1h['Open'].iloc[-2] else None
    
    # FVG simple check
    fvg_bull = float(df1h['Low'].iloc[-1]) > float(df1h['High'].iloc[-3])
    fvg_bear = float(df1h['High'].iloc[-1]) < float(df1h['Low'].iloc[-3])

    # 3. 15M CONFIRMATION ONLY
    close_15 = float(df15['Close'].iloc[-1])
    high_15 = float(df15['High'].iloc[-10:-1].max())
    low_15 = float(df15['Low'].iloc[-10:-1].min())
    
    confirm_bull = close_15 > high_15
    confirm_bear = close_15 < low_15

    # Fibonacci Bonus Rating (0.5 - 0.79)
    fib_range = swing_high_1h - swing_low_1h
    fib_05 = swing_low_1h + fib_range * 0.5
    fib_079 = swing_low_1h + fib_range * 0.79
    fib_rating = "High" if fib_05 <= close_1h <= fib_079 or fib_05 <= close_15 <= fib_079 else "Medium"

    signal = None
    if trend_4h == "BULLISH" and swept_low and bos_bull and confirm_bull:
        signal = "BUY"
        entry_zone = bullish_ob if bullish_ob else close_1h
        reason = f"4H {trend_4h} | 1H swept {swing_low_1h:.2f} liquidity + BOS above {recent_high_1h:.2f} | OB/FVG at {entry_zone:.2f} | 15M Confirmed | Fib Rating: {fib_rating}"
        sl_level = swing_low_1h
    elif trend_4h == "BEARISH" and swept_high and bos_bear and confirm_bear:
        signal = "SELL"
        entry_zone = bearish_ob if bearish_ob else close_1h
        reason = f"4H {trend_4h} | 1H swept {swing_high_1h:.2f} liquidity + BOS below {recent_low_1h:.2f} | OB/FVG at {entry_zone:.2f} | 15M Confirmed | Fib Rating: {fib_rating}"
        sl_level = swing_high_1h
    else:
        return None

    entry = close_15
    if signal == "BUY":
        risk = entry - sl_level
        if risk <= 0: return None
        tp1 = entry + risk * RR1
        tp2 = entry + risk * RR2
        tp3 = entry + risk * RR3
    else:
        risk = sl_level - entry
        if risk <= 0: return None
        tp1 = entry - risk * RR1
        tp2 = entry - risk * RR2
        tp3 = entry - risk * RR3

    return signal, entry, sl_level, tp1, tp2, tp3, reason, fib_rating

def loop():
    send_msg(f"✅ *kobby_btcbot LIVE*\nStrategy: SMC | 4H Trend + 1H Liq Sweep+BOS+OB/FVG + 15M Confirm | RR 1:{RR1},1:{RR2},1:{RR3}\nFib Bonus")
    last_sent = 0
    while True:
        try:
            res = get_smc_setup()
            if res and (time.time() - last_sent > 3600): # 1hr cooldown
                sig, entry, sl, tp1, tp2, tp3, reason, fib = res
                msg = f"""⚡️ *BTCUSD {sig} ENTRY - SMC*

*Entry:* {entry:.2f}
*SL:* {sl:.2f}
*TP1:* {tp1:.2f} (1:{RR1})
*TP2:* {tp2:.2f} (1:{RR2})
*TP3:* {tp3:.2f} (1:{RR3})

*Top Down:* {reason}
"""
                send_msg(msg)
                last_sent = time.time()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1800) # check every 30min

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    loop()
