def get_pip(pair):
    return 0.1

def calc_lot_size(balance, risk_percent, entry, sl, pair):
    risk = balance * (risk_percent / 100)
    dist = abs(entry - sl)
    if dist == 0:
        return 0.01
    lot = risk / (dist * 10)
    return round(max(0.01, min(lot, 2.0)), 2)

def calc_lot(balance, risk_percent, entry, sl, pair):
    return calc_lot_size(balance, risk_percent, entry, sl, pair)

def generate_entry(pair, bias, current_price, sl_price, balance=1000, risk_percent=1, source="PURE-SMC"):
    if not sl_price:
        return None
    buff = 0.1 * 30
    sl = sl_price - buff if bias == "BUY" else sl_price + buff
    dist = abs(current_price - sl)
    if bias == "BUY":
        tp1 = current_price + dist * 2
        tp2 = current_price + dist * 3
        tp3 = current_price + dist * 5
        typ = "BUY"
    else:
        tp1 = current_price - dist * 2
        tp2 = current_price - dist * 3
        tp3 = current_price - dist * 5
        typ = "SELL"
    lot = calc_lot_size(balance, risk_percent, current_price, sl, pair)
    return {
        "pair": pair,
        "type": typ,
        "bias": bias,
        "entry": current_price,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "lot": lot,
        "alert_message": f"🔫 {typ} {pair} @ {current_price:.2f}\n🛑 SL: {sl:.2f}\n🎯 TP1: {tp1:.2f} (1:2)\n🎯 TP2: {tp2:.2f} (1:3)\n🎯 TP3: {tp3:.2f} (1:5)\n📦 Lot: {lot} (1% Risk)\n📊 {source}"
    }

# backward compat - fixes ImportError
def get_entry_levels(pair, bias, current_price, sl_price, balance=1000, risk_percent=1, source="PURE-SMC"):
    return generate_entry(pair, bias, current_price, sl_price, balance, risk_percent, source)

def get_entry(pair, bias, current_price, sl_price, balance=1000, risk_percent=1, source="PURE-SMC"):
    return generate_entry(pair, bias, current_price, sl_price, balance, risk_percent, source)
