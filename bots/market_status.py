import requests

import os
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

# BOT 4: MARKET STATUS + SESSION ALERTS - ALL YOUR 10 PAIRS
# Alerts: Market Open/Close + Session Open (London, NY, Asia)

import datetime

# YOUR PAIRS GROUP
PAIRS_BY_MARKET = {
    "FOREX": ["GBPUSD", "GBPJPY", "AUDCAD", "EURUSD", "AUDUSD", "USDJPY"],
    "GOLD": ["XAUUSD"],
    "CRYPTO": ["BTCUSD"],
    "INDICES": ["NAS100", "SPX500", "SPX", "US30"]
}

# Market Hours in GMT
MARKET_HOURS = {
    "FOREX": {"open_day": 0, "open_hour": 22, "close_day": 4, "close_hour": 21}, # Sun 22:00 - Fri 21:00 GMT
    "GOLD": {"open_day": 0, "open_hour": 22, "close_day": 4, "close_hour": 21},
    "CRYPTO": {"open_day": None, "open_hour": None}, # 24/7
    "INDICES": {"open_hour": 13, "open_min": 30, "close_hour": 20, "close_min": 0} # Mon-Fri 13:30-20:00 GMT
}

# Trading Sessions GMT
SESSIONS = {
    "SYDNEY": {"start": (21, 0), "end": (6, 0), "pairs": ["AUDUSD", "AUDCAD"]},
    "TOKYO": {"start": (0, 0), "end": (9, 0), "pairs": ["GBPJPY", "USDJPY"]},
    "LONDON": {"start": (7, 0), "end": (16, 0), "pairs": ["GBPUSD", "EURUSD", "GBPJPY", "XAUUSD"]},
    "NEW YORK": {"start": (12, 0), "end": (21, 0), "pairs": ["GBPUSD", "EURUSD", "XAUUSD", "BTCUSD", "NAS100", "SPX500"]},
    "OVERLAP LONDON/NY": {"start": (12, 0), "end": (16, 0), "pairs": ["GBPUSD", "EURUSD", "XAUUSD"]}
}

def get_current_gmt():
    return datetime.datetime.utcnow()

def is_forex_market_open():
    now = get_current_gmt()
    # Sunday = 6, Monday = 0... in Python weekday Monday=0
    weekday = now.weekday()
    hour = now.hour

    # Closed Friday 21:00 to Sunday 22:00
    if weekday == 4 and hour >= 21: # Friday after 21
        return False
    if weekday == 5: # Saturday
        return False
    if weekday == 6 and hour < 22: # Sunday before 22
        return False
    return True

def is_market_open_for_pair(pair):
    pair = pair.upper()
    if "BTC" in pair:
        return True, "24/7 OPEN"

    if pair in ["NAS100", "SPX500", "SPX", "US30"]:
        now = get_current_gmt()
        if now.weekday() >= 5: # Weekend
            return False, f"🔴 {pair} CLOSED - Weekend"
        if 13 <= now.hour < 20 or (now.hour==13 and now.minute>=30):
            return True, f"🟢 {pair} OPEN - US Session"
        else:
            return False, f"🔴 {pair} CLOSED - Opens 13:30 GMT"

    # Forex & Gold
    if is_forex_market_open():
        return True, f"🟢 {pair} OPEN"
    else:
        return False, f"🔴 {pair} CLOSED - Forex Weekend"

def check_all_pairs_status():
    """Check status for ALL your 10 pairs"""
    now = get_current_gmt()
    status = {}
    alerts = []

    all_pairs = ["GBPUSD","GBPJPY","XAUUSD","AUDCAD","EURUSD","AUDUSD","USDJPY","BTCUSD","NAS100","SPX500"]

    for pair in all_pairs:
        open_, msg = is_market_open_for_pair(pair)
        status[pair] = {"open": open_, "msg": msg}
        if not open_:
            alerts.append(msg)

    return status, alerts

def check_session_status():
    """Check which trading session is open now"""
    now = get_current_gmt()
    current_h = now.hour
    current_m = now.minute
    current_minutes = current_h * 60 + current_m

    active_sessions = []
    session_alerts = []

    for name, data in SESSIONS.items():
        s_h, s_m = data["start"]
        e_h, e_m = data["end"]
        start_min = s_h * 60 + s_m
        end_min = e_h * 60 + e_m

        # Handle overnight sessions like Sydney
        if start_min > end_min: # overnight
            is_active = current_minutes >= start_min or current_minutes < end_min
        else:
            is_active = start_min <= current_minutes < end_min

        if is_active:
            active_sessions.append(name)
            pairs = ",".join(data["pairs"])
            session_alerts.append(f"🟢 {name} SESSION OPEN - Best for: {pairs}")

    if not active_sessions:
        return [], ["⚪ No major session - Low volatility"]

    return active_sessions, session_alerts

def get_market_status_alert():
    """Full alert used by main.py - runs every hour"""
    now = get_current_gmt()
    time_str = now.strftime("%H:%M GMT %A")

    pair_status, pair_alerts = check_all_pairs_status()
    active_sessions, session_alerts = check_session_status()

    # Build message
    msg = f"⏰ MARKET STATUS - {time_str}\n\n"

    # Pairs
    msg += "PAIRS:\n"
    for pair, data in pair_status.items():
        msg += f"{data['msg']}\n"

    msg += "\nSESSIONS:\n"
    for alert in session_alerts:
        msg += f"{alert}\n"

    # Best time to trade
    if "LONDON" in active_sessions or "NEW YORK" in active_sessions:
        msg += "\n🔥 BEST TIME TO TRADE GBPUSD, XAUUSD, EURUSD NOW!"
    if "TOKYO" in active_sessions:
        msg += "\n🔥 BEST TIME FOR JPY PAIRS: GBPJPY, USDJPY"
    if "SYDNEY" in active_sessions:
        msg += "\n🔥 BEST TIME FOR AUD PAIRS: AUDUSD, AUDCAD"

    return {
        "time": time_str,
        "pair_status": pair_status,
        "active_sessions": active_sessions,
        "alerts": pair_alerts + session_alerts,
        "full_message": msg,
        "forex_open": is_forex_market_open()
    }

# Quick functions for main.py
def is_trading_allowed(pair="GBPUSD"):
    """Check if we can trade this pair now"""
    open_, _ = is_market_open_for_pair(pair)
    return open_

def get_current_session():
    """Get current best session"""
    active, _ = check_session_status()
    return active
