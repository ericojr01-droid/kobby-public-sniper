import datetime

def check_session_status():
    now = datetime.datetime.utcnow()
    h = now.hour
    active = []
    if 7 <= h < 16: active.append("LONDON")
    if 12 <= h < 21: active.append("NEW YORK")
    if 0 <= h < 9: active.append("TOKYO")
    if 21 <= h or h < 6: active.append("SYDNEY")
    return active, [f"🟢 {s} OPEN" for s in active]

def is_forex_market_open():
    now = datetime.datetime.utcnow()
    return now.weekday()!= 5

def is_trading_allowed(pair="XAUUSD"):
    return True
