import requests
import pytz
from datetime import datetime, timedelta

cached = []
last = None

def analyze_fundamental(pair):
    global cached, last
    try:
        if last and datetime.now() - last < timedelta(minutes=15):
            news = cached
        else:
            r = requests.get("https://nfs.faireconomy.media/ff_calendar_thisweek.json", timeout=10)
            data = r.json()
            news = [e for e in data if e.get("impact") == "High" and e.get("currency") == "USD"]
            cached = news
            last = datetime.now()
        
        now = datetime.now(pytz.utc)
        for n in news:
            title = n.get("title","").lower()
            if not any(x in title for x in ["cpi","fomc","nfp","nonfarm","interest","gdp"]):
                continue
            try:
                nt = datetime.fromisoformat(n["time"].replace("Z","+00:00"))
                if nt - timedelta(minutes=60) <= now <= nt + timedelta(minutes=60):
                    return {"block_type": "BLOCK", "alert_message": f"🔴 USD {n['title']} BLOCK"}
            except:
                continue
    except Exception as e:
        print(f"News fetch fail {e} - allowing trade", flush=True)
    
    return {"block_type": "CLEAR", "alert_message": ""}
