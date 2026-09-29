import requests
from datetime import datetime, timedelta
import pytz

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

# Your 10 pairs mapping to currencies
PAIR_CURRENCY_MAP = {
    "GBPUSD": ["GBP", "USD"],
    "GBPJPY": ["GBP", "JPY"],
    "XAUUSD": ["USD"], # Gold moves with USD news
    "AUDCAD": ["AUD", "CAD"],
    "EURUSD": ["EUR", "USD"],
    "AUDUSD": ["AUD", "USD"],
    "USDJPY": ["USD", "JPY"],
    "BTCUSD": ["USD", "BTC"], # Special handling
    "NAS100": ["USD"],
    "SPX500": ["USD"]
}

cached_news = []
last_fetch_time = None

def fetch_forex_factory_news():
    """
    Fetch real-time high impact news from Forex Factory
    Using free Faireconomy API (official ForexFactory feed)
    """
    global cached_news, last_fetch_time
    
    # Cache for 15 mins to avoid too many requests
    if last_fetch_time and datetime.now() - last_fetch_time < timedelta(minutes=15):
        return cached_news
        
    try:
        # Real-time feed - same data as forexfactory.com
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        high_impact = []
        for event in data:
            if event.get("impact") == "High": # Only RED folder
                high_impact.append({
                    "currency": event.get("currency"),
                    "title": event.get("title"),
                    "time": event.get("date"), # ISO time
                    "impact": "High"
                })
        
        cached_news = high_impact
        last_fetch_time = datetime.now()
        return high_impact
        
    except Exception as e:
        print(f"Fundamental fetch error: {e}")
        return cached_news # Return last cache if error

def fetch_crypto_news():
    """Check for high impact crypto news - for BTCUSD"""
    try:
        # Using CryptoPanic or simple check - you can add API key later
        # For now we check if major BTC moving news exists via CoinGecko status
        # We treat US High impact as BTC blocker too (Fed, CPI affects BTC)
        return [] # Placeholder - USD news will block BTC already
    except:
        return []

def is_news_block_active(pair):
    """
    Check if trading should be BLOCKED for a pair due to news
    Returns: (blocked: bool, message: str, news_title: str)
    """
    forex_news = fetch_forex_factory_news()
    currencies_to_check = PAIR_CURRENCY_MAP.get(pair, [])
    
    now_utc = datetime.now(pytz.utc)
    
    for news in forex_news:
        if news["currency"] not in currencies_to_check:
            continue
            
        try:
            # Parse news time
            news_time = datetime.fromisoformat(news["time"].replace("Z", "+00:00"))
            
            # Block 30 mins before and 30 mins after
            block_start = news_time - timedelta(minutes=30)
            block_end = news_time + timedelta(minutes=30)
            
            if block_start <= now_utc <= block_end:
                minutes_to_news = int((news_time - now_utc).total_seconds() / 60)
                
                if minutes_to_news > 0:
                    msg = f"🔴 {news['currency']} HIGH IMPACT NEWS IN {minutes_to_news}MINS - TRADING BLOCKED: {news['title']}"
                else:
                    msg = f"🔴 {news['currency']} NEWS LIVE - TRADING BLOCKED: {news['title']} - Wait {abs(minutes_to_news) + 30} mins"
                
                return True, msg, news["title"]
                
        except Exception as e:
            continue
    
    return False, "", ""

def analyze_fundamental(pair):
    """
    MAIN FUNCTION for your bot - Use this in main.py
    Technical = TradingView, Fundamental = ForexFactory + Crypto
    """
    blocked, alert_msg, news_title = is_news_block_active(pair)
    
    if blocked:
        return {
            "pair": pair,
            "allow_trading": False,
            "source": "FUNDAMENTAL",
            "alert_message": alert_msg,
            "news": news_title,
            "block_type": "NEWS_BLOCK"
        }
    else:
        # Check for upcoming news (warning, not block yet)
        forex_news = fetch_forex_factory_news()
        currencies = PAIR_CURRENCY_MAP.get(pair, [])
        now_utc = datetime.now(pytz.utc)
        
        for news in forex_news:
            if news["currency"] in currencies:
                try:
                    news_time = datetime.fromisoformat(news["time"].replace("Z", "+00:00"))
                    mins_until = int((news_time - now_utc).total_seconds() / 60)
                    if 30 < mins_until <= 60: # Warning 60 to 30 mins before
                        return {
                            "pair": pair,
                            "allow_trading": True,
                            "source": "FUNDAMENTAL",
                            "alert_message": f"⚠️ WARNING: {news['currency']} High Impact in {mins_until} mins - {news['title']} - Be careful",
                            "news": news["title"],
                            "block_type": "WARNING"
                        }
                except:
                    pass
        
        return {
            "pair": pair,
            "allow_trading": True,
            "source": "FUNDAMENTAL",
            "alert_message": "",
            "news": None,
            "block_type": "CLEAR"
        }

# For testing
if __name__ == "__main__":
    for p in ["GBPUSD", "BTCUSD", "XAUUSD"]:
        result = analyze_fundamental(p)
        print(result)
