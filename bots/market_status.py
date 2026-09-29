import datetime

last_active_sessions = set()
market_was_open = None

def check_session_status():
    global last_active_sessions
    now = datetime.datetime.utcnow()
    h = now.hour
    active = []
    if 7 <= h < 16:
        active.append("LONDON")
    if 12 <= h < 21:
        active.append("NEW YORK")
    if 0 <= h < 9:
        active.append("TOKYO")
    if 21 <= h or h < 6:
        active.append("SYDNEY")
    
    new_sessions = [s for s in active if s not in last_active_sessions]
    last_active_sessions = set(active)
    
    return active, new_sessions

def is_forex_market_open():
    now = datetime.datetime.utcnow()
    weekday = now.weekday()
    # Forex closes Friday 22:00 GMT and opens Sunday 22:00 GMT
    # Simplified: closed Saturday
    if weekday == 5:  # Saturday
        return False
    if weekday == 6 and now.hour < 22:  # Sunday before 22:00
        return False
    if weekday == 4 and now.hour >= 22:  # Friday after 22:00
        return False
    return True

def should_send_session_alert():
    active, new_sessions = check_session_status()
    if new_sessions:
        return True, new_sessions
    return False, []

def should_send_market_open_close_alert():
    global market_was_open
    is_open = is_forex_market_open()
    
    if market_was_open is None:
        market_was_open = is_open
        return False, None
    
    if market_was_open != is_open:
        market_was_open = is_open
        if is_open:
            return True, "OPEN"
        else:
            return True, "CLOSE"
    
    return False, None

def is_trading_allowed(pair="XAUUSD"):
    return is_forex_market_open()

def get_session_status_message(new_sessions):
    if not new_sessions:
        return None
    msgs = [f"🟢 {s} SESSION OPEN" for s in new_sessions]
    return "\n".join(msgs)
