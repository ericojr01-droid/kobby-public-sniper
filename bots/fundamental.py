# BOT 2: FUNDAMENTAL NEWS TRADER + PROTECTOR + ALERTS - ALL PAIRS VERSION
import datetime

# YOUR PAIRS: GBPUSD GBPJPY XAUUSD AUDCAD EURUSD AUDUSD USDJPY BTCUSD NAS100 SPX
PAIR_IMPACT = {
    "GBPUSD": ["USD", "GBP"],
    "GBPJPY": ["GBP", "JPY"],
    "XAUUSD": ["USD", "XAU"],
    "AUDCAD": ["AUD", "CAD"],
    "EURUSD": ["USD", "EUR"],
    "AUDUSD": ["USD", "AUD"],
    "USDJPY": ["USD", "JPY"],
    "BTCUSD": ["USD", "BTC", "CRYPTO"],
    "NAS100": ["USD", "US"],
    "NAS": ["USD", "US"],
    "SPX500": ["USD", "US"],
    "SPX": ["USD", "US"],
    "US30": ["USD", "US"],
}

def get_todays_news():
    """HIGH impact news for ALL your markets - Later connect real ForexFactory API"""
    now = datetime.datetime.utcnow()
    todays = [
        # USD affects 8 of your pairs
        {"time": "12:30", "currency": "USD", "event": "CPI y/y", "impact": "HIGH", "pairs": ["GBPUSD","XAUUSD","EURUSD","AUDUSD","USDJPY","BTCUSD","NAS100","SPX500"]},
        {"time": "13:15", "currency": "USD", "event": "NFP / Jobs", "impact": "HIGH", "pairs": ["GBPUSD","XAUUSD","EURUSD","AUDUSD","USDJPY","NAS100","SPX500"]},
        {"time": "14:00", "currency": "USD", "event": "FOMC / Interest Rate", "impact": "HIGH", "pairs": ["GBPUSD","XAUUSD","EURUSD","USDJPY","BTCUSD","NAS100","SPX500"]},
        {"time": "18:00", "currency": "USD", "event": "Fed Powell Speech", "impact": "HIGH", "pairs": ["GBPUSD","XAUUSD","EURUSD","AUDUSD","USDJPY","BTCUSD","NAS100","SPX500"]},
        # GBP affects 2 pairs
        {"time": "08:30", "currency": "GBP", "event": "GDP / CPI / Jobs", "impact": "HIGH", "pairs": ["GBPUSD","GBPJPY"]},
        # EUR affects 1 pair
        {"time": "07:15", "currency": "EUR", "event": "ECB Rate Decision", "impact": "HIGH", "pairs": ["EURUSD"]},
        # AUD affects 2 pairs
        {"time": "01:30", "currency": "AUD", "event": "AUD Jobs / CPI", "impact": "HIGH", "pairs": ["AUDUSD","AUDCAD"]},
        # CAD affects 1 pair
        {"time": "12:30", "currency": "CAD", "event": "CAD Oil / CPI", "impact": "HIGH", "pairs": ["AUDCAD"]},
        # JPY affects 2 pairs
        {"time": "23:50", "currency": "JPY", "event": "BOJ Interest Rate", "impact": "HIGH", "pairs": ["GBPJPY","USDJPY"]},
        # BTC / Crypto
        {"time": "15:00", "currency": "BTC", "event": "BTC Risk Sentiment", "impact": "HIGH", "pairs": ["BTCUSD"]},
    ]
    return todays

def check_upcoming_news(pair="XAUUSD", minutes_ahead=15):
    """Check if high impact news coming for THAT pair in next X minutes"""
    now = datetime.datetime.utcnow()
    news_list = get_todays_news()
    
    for news in news_list:
        if pair in news.get("pairs", []) and news["impact"]=="HIGH":
            h, m = map(int, news["time"].split(":"))
            news_time = now.replace(hour=h, minute=m, second=0)
            diff = (news_time - now).total_seconds() / 60

            if 0 <= diff <= minutes_ahead:
                return True, f"⚠️ {news['currency']} {news['event']} in {int(diff)}min! Affects {pair} - Close trades!"
            if -5 <= diff <= 5:
                return True, f"🔴 NEWS LIVE NOW: {news['currency']} {news['event']} - DO NOT TRADE {pair}"

    return False, "Safe - No upcoming news"

def check_open_trades_protection(open_trades):
    """Alert if news go affect open trades - open_trades = [{'pair':'XAUUSD','type':'BUY'}]"""
    alerts = []
    for trade in open_trades:
        pair = trade["pair"]
        is_risky, msg = check_upcoming_news(pair, minutes_ahead=30)
        if is_risky:
            alerts.append(f"🚨 CLOSE ALERT: {pair} {trade['type']} | {msg}")
    return alerts

def analyze_fundamental_for_entry(pair, candles_15m, candles_5m):
    """Trade news 5 mins AFTER release - momentum"""
    is_risky, msg = check_upcoming_news(pair, minutes_ahead=15)
    if is_risky:
        return {"setup": False, "reason": f"News block: {msg}"}

    if len(candles_5m) < 10:
        return {"setup": False, "reason": "Not enough data after news"}

    last_close = candles_5m[-1]['close']
    prev_close = candles_5m[-6]['close']
    momentum = (last_close - prev_close) / prev_close * 100

    if abs(momentum) < 0.15:
        return {"setup": False, "reason": f"Weak momentum {momentum:.2f}% after news"}

    bias = "BULLISH" if momentum > 0 else "BEARISH"
    return {
        "setup": True,
        "bias": bias,
        "final": bias,
        "reason": f"News momentum {momentum:.2f}% -> {bias}",
        "momentum": momentum
    }

def get_daily_news_alert():
    """7AM GMT daily news briefing for all your pairs"""
    news = get_todays_news()
    if not news:
        return "📰 No HIGH impact news today - Safe to trade all day!"

    msg = "📰 TODAY'S HIGH IMPACT NEWS (GMT):\n"
    for n in news:
        pairs_str = ",".join(n['pairs'])
        msg += f"⏰ {n['time']} - {n['currency']} {n['event']} -> {pairs_str}\n"
    msg += "\n⚠️ Bot will alert 15min before each!"
    return msg

def analyze_fundamental(pair="XAUUSD", candles_15m=None, candles_5m=None, open_trades=[]):
    protection_alerts = check_open_trades_protection(open_trades)
    is_blocked, block_msg = check_upcoming_news(pair, 15)

    if is_blocked:
        return {
            "setup": False,
            "final": "NO TRADE - NEWS",
            "alerts": protection_alerts,
            "block_reason": block_msg,
            "daily": get_daily_news_alert()
        }

    if candles_15m and candles_5m:
        entry_signal = analyze_fundamental_for_entry(pair, candles_15m, candles_5m)
        entry_signal["alerts"] = protection_alerts
        entry_signal["daily"] = get_daily_news_alert()
        return entry_signal

    return {
        "setup": False,
        "final": "NO SETUP",
        "alerts": protection_alerts,
        "daily": get_daily_news_alert()
}
