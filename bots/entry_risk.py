import requests

BOT_TOKEN = "8826207602:AAEnJMlJOb6lW1QHV4aJ9E8edPacTprTE_Q"
CHAT_ID = "8240862120"
CHANNEL_ID = "@KobbyforexTrade"

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data1 = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, data=data1, timeout=10)
        data2 = {"chat_id": CHANNEL_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, data=data2, timeout=10)
    except:
        pass

# BOT 3: ENTRY + RISK MANAGEMENT + 3 TPS - ALL PAIRS
# Risk 1% | TP1 1:2 | TP2 1:3 | TP3 1:5

def get_pip_value(pair):
    """Pip / point value for different markets"""
    pair = pair.upper()
    if "XAU" in pair or "GOLD" in pair:
        return 0.1  # Gold moves in 0.1
    if "JPY" in pair:
        return 0.01
    if "BTC" in pair:
        return 1.0
    if "NAS" in pair or "SPX" in pair or "US30" in pair:
        return 1.0
    return 0.0001  # Forex majors

def calculate_lot_size(balance, risk_percent, entry, sl, pair):
    """Calculate lot based on 1% risk"""
    risk_amount = balance * (risk_percent / 100)
    sl_distance = abs(entry - sl)
    
    if sl_distance == 0:
        return 0.01
    
    pip_val = get_pip_value(pair)
    pips = sl_distance / pip_val
    
    # Lot formula simplified for all markets
    # Forex: lot = risk / (sl_pips * $10)
    # Gold/BTC/Index: adjust
    if pair in ["XAUUSD", "BTCUSD", "NAS100", "SPX500", "SPX"]:
        # For gold/BTC, $1 move = $1 per 0.01 lot approx
        lot = risk_amount / (sl_distance * 100)
    else:
        lot = risk_amount / (pips * 10)
    
    # Safety limits
    lot = max(0.01, min(lot, 5.0))
    return round(lot, 2)

def get_entry_levels(analysis_result, current_price, balance=1000, risk_percent=1):
    """
    analysis_result from BOT 1 or BOT 2
    Example: {"setup":True, "bias":"BULLISH", "pair":"GBPUSD", "source":"TECHNICAL"}
    """
    if not analysis_result.get("setup"):
        return None

    pair = analysis_result.get("pair", "XAUUSD")
    bias = analysis_result.get("bias", "BULLISH")
    source = analysis_result.get("source", "TECHNICAL")  # TECHNICAL or FUNDAMENTAL
    
    # SL calculation - SMC style buffer
    pip_val = get_pip_value(pair)
    
    # Default SL distances if no OB level provided
    default_sl_pips = {
        "GBPUSD": 25, "GBPJPY": 30, "XAUUSD": 50,  # 5$ = 50 pips
        "AUDCAD": 25, "EURUSD": 20, "AUDUSD": 20,
        "USDJPY": 25, "BTCUSD": 200, "NAS100": 80, "SPX500": 20
    }
    
    sl_pips = default_sl_pips.get(pair, 25)
    sl_dist = sl_pips * pip_val
    
    if bias == "BULLISH":
        sl = current_price - sl_dist
        tp1 = current_price + (sl_dist * 2)  # 1:2
        tp2 = current_price + (sl_dist * 3)  # 1:3
        tp3 = current_price + (sl_dist * 5)  # 1:5
        entry_type = "BUY"
    else:
        sl = current_price + sl_dist
        tp1 = current_price - (sl_dist * 2)
        tp2 = current_price - (sl_dist * 3)
        tp3 = current_price - (sl_dist * 5)
        entry_type = "SELL"

    lot = calculate_lot_size(balance, risk_percent, current_price, sl, pair)

    # Build final message - NO EXPLANATION, just source tag
    if source == "FUNDAMENTAL":
        analysis_tag = "FUNDAMENTAL ANALYSIS"
    else:
        analysis_tag = "TECHNICAL ANALYSIS"

    return {
        "pair": pair,
        "type": entry_type,
        "bias": bias,
        "entry": current_price,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "lot": lot,
        "risk_percent": risk_percent,
        "rr": "1:2, 1:3, 1:5",
        "analysis_source": analysis_tag,
        "alert_message": f"🔫 {entry_type} {pair} @ {current_price:.5f}\n🛑 SL: {sl:.5f}\n🎯 TP1: {tp1:.5f} (1:2)\n🎯 TP2: {tp2:.5f} (1:3)\n🎯 TP3: {tp3:.5f} (1:5)\n📦 Lot: {lot} (1% Risk)\n📊 {analysis_tag}"
    }

# Main wrapper used by main.py
def generate_entry(pair, bias, current_price, source="TECHNICAL", balance=1000):
    """
    Quick entry generator
    source = "TECHNICAL" or "FUNDAMENTAL"
    """
    result = {
        "setup": True,
        "bias": bias,
        "pair": pair,
        "source": source
    }
    return get_entry_levels(result, current_price, balance, 1)
