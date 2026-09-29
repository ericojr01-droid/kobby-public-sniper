def generate_entry(pair, bias, current_price, sl_price, source="SMC-4H-1H-15M"):
    if not sl_price or not current_price:
        return None
    
    buff = 3.0
    sl = sl_price - buff if bias == "BUY" else sl_price + buff
    dist = abs(current_price - sl)
    
    if dist == 0:
        return None

    if bias == "BUY":
        tp1 = current_price + dist * 2
        tp2 = current_price + dist * 3
        tp3 = current_price + dist * 5
    else:
        tp1 = current_price - dist * 2
        tp2 = current_price - dist * 3
        tp3 = current_price - dist * 5

    alert = (
        f"🔫 {bias} {pair} @ {current_price:.2f}\n"
        f"🛑 SL: {sl:.2f}\n"
        f"🎯 TP1: {tp1:.2f} (1:2)\n"
        f"🎯 TP2: {tp2:.2f} (1:3)\n"
        f"🎯 TP3: {tp3:.2f} (1:5)\n"
        f"📊 {source}"
    )
    
    return {
        "pair": pair,
        "bias": bias,
        "entry": current_price,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "alert_message": alert
    }

# backward compat for old imports
def get_entry_levels(pair, bias, current_price, sl_price, balance=1000, risk_percent=1, source="SMC-4H-1H-15M"):
    return generate_entry(pair, bias, current_price, sl_price, source)

def get_entry(pair, bias, current_price, sl_price, balance=1000, risk_percent=1, source="SMC-4H-1H-15M"):
    return generate_entry(pair, bias, current_price, sl_price, source)

def calc_lot_size(balance, risk_percent, entry, sl, pair):
    return 0.01

def calc_lot(balance, risk_percent, entry, sl, pair):
    return 0.01

def get_pip(pair):
    return 0.1
