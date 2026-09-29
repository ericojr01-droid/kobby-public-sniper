def get_pip(pair):
    return 0.1

def calc_lot_size(balance, risk_percent, entry, sl, pair):
    dist = abs(entry - sl)
    if dist == 0:
        return 0.01
    risk_amount = balance * (risk_percent / 100)
    lot = risk_amount / (dist * 10)
    lot = max(0.01, min(lot, 2.0))
    return round(lot, 2)

def calc_lot(balance, risk_percent, entry, sl, pair):
    return calc_lot_size(balance, risk_percent, entry, sl, pair)

def generate_entry(pair, bias, current_price, sl_price, balance=1000, risk_percent=1, source="PURE-SMC"):
    if not sl_price:
        return None
    buff = 3.0
    sl = sl_price - buff if bias == "BUY" else sl_price + buff
    dist = abs(current_price - sl)
    if bias == "BUY":
        tp1 = current_price + dist * 2
        tp2 = current_price + dist * 3
        tp3 = current_price + dist * 5
    else:
        tp1 = current_price - dist * 2
        tp2 = current_price - dist * 3
        tp3 = current_price - dist * 5
    lot = calc_lot_size(balance, risk_percent, current_price, sl, pair)
    alert = f"🔫 {bias} {pair} @ {current_price:.2f}\n🛑 SL: {sl:.2f}\n🎯 TP1: {tp1:.2f}\n🎯 TP2: {tp2:.2f}\n🎯 TP3: {tp3:.2f}\n📦 Lot: {lot}"
    return {"alert_message": alert}

def get_entry_levels(pair, bias, current_price, sl_price, balance=1000, risk_percent=1, source=""):
    return generate_entry(pair, bias, current_price, sl_price, balance, risk_percent, source)

def get_entry(pair, bias, current_price, sl_price, balance=1000, risk_percent=1, source=""):
    return generate_entry(pair, bias, current_price, sl_price, balance, risk_percent, source)
