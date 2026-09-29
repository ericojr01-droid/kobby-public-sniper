import requests
import pytz
from datetime import datetime, timedelta

PAIR_CURRENCY_MAP = {
    "GBPUSD": ["GBP", "USD"],
    "GBPJPY": ["GBP", "JPY"],
    "XAUUSD": ["USD"],
    "AUDCAD": ["AUD", "CAD"],
    "EURUSD": ["EUR", "USD"],
    "AUDUSD": ["AUD", "USD"],
    "USDJPY": ["USD", "JPY"],
    "BTCUSD": ["USD"],
    "NAS100": ["USD"],
    "SPX500": ["USD"]
}

cached = []
last = None

def fetch_news():
    global cached, last
    if last and datetime.now() - last < timedelta(minutes=15):
        return cached
    try:
        r = requests.get("https://nfs.faireconomy.media/ff_calendar_thisweek.json", timeout=10)
        data = r.json()
        high = []
        for e in data:
            if e.get("impact") == "High":
                high.append({"currency": e.get("currency"), "title": e.get("title"), "time": e.get("date")})
        cached = high
        last = datetime.now()
        return high
    except:
        return cached

def is_news_block_active(pair):
    news = fetch_news()
    currs = PAIR_CURRENCY_MAP.get(pair, [])
    now = datetime.now(pytz.utc)
    for n in news:
        if n["currency"] not in currs:
            continue
        title = n["title"].lower()
        if not any(x in title for x in ["cpi", "fomc", "interest", "nfp", "nonfarm", "gdp", "ppi"]):
            continue
        try:
            nt = datetime.fromisoformat(n["time"].replace("Z", "+00:00"))
            if nt - timedelta(minutes=60) <= now <= nt + timedelta(minutes=60):
                mins = int((nt - now).total_seconds() / 60)
                return True, f"🔴 {n['currency']} {n['title']} in {mins}min BLOCK 60m", n["title"]
        except:
            continue
    return False, "", ""

def analyze_fundamental(pair):
    blocked, msg, title = is_news_block_active(pair)
    if blocked:
        return {"pair": pair, "allow_trading": False, "alert_message": msg, "block_type": "BLOCK", "news": title}
    return {"pair": pair, "allow_trading": True, "alert_message": "", "block_type": "CLEAR", "news": None}
