import os

def get_pip(pair):
    p = pair.upper()
    if "XAU" in p:
        return 0.1
    if "JPY" in p:
        return 0.01
    if "BTC" in p or "NAS" in p or "SPX" in p:
        return 1.0
    return 0.0001

def calc_lot(balance, risk_percent, entry, sl, pair):
    risk = balance * (risk_percent / 100)
    dist = abs(entry - sl)
    if dist == 0:
        return 0.01
    pip = get_pip(pair)
    pips = dist / pip
    if "XAU" in pair:
        lot = risk / (dist * 10)
    elif pair in ["BTCUSD", "NAS100", "SPX500"]:
        lot = risk / (dist * 1)
    else:
        lot = risk / (pips * 10)
    return round(max(0.01, min(lot, 2.0)), 2)

def generate_entry(pair, bias, current_price, sl_price, balance=1000, risk_percent=1, source="PURE-SMC"):
    if not sl_price:
        return None
    pip = get_pip(pair)
    buff = pip * 15 if "XAU" not in pair and pair not in ["BTCUSD", "NAS100", "SPX500"] else pip * 30
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
    lot = calc_lot(balance, risk_percent, current_price, sl, pair)
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
        "alert_message": f"🔫 {typ} {pair} @ {current_price:.5f}\n🛑 SL: {sl:.5f} (Sweep+Buff)\n🎯 TP1: {tp1:.5f} (1:2)\n🎯 TP2: {tp2:.5f} (1:3)\n🎯 TP3: {tp3:.5f} (1:5)\n📦 Lot: {lot} (1% Risk)\n📊 {source}"
    }
