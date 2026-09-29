import requests
import pytz
from datetime import datetime, timedelta

try:
    import yfinance as yf
except:
    yf = None

cached_news = []
last_fetch = None
last_fund_bias = {"bias": "NEUTRAL", "reason": "No data yet"}

def fetch_forexfactory_news():
    global cached_news, last_fetch
    if last_fetch and datetime.now() - last_fetch < timedelta(minutes=15):
        return cached_news
    try:
        r = requests.get("https://nfs.faireconomy.media/ff_calendar_thisweek.json", timeout=15)
        data = r.json()
        high_usd = []
        for e in data:
            if e.get("impact") == "High" and e.get("currency") == "USD":
                high_usd.append(e)
        cached_news = high_usd
        last_fetch = datetime.now()
        return high_usd
    except Exception as e:
        print(f"FF fetch fail: {e}", flush=True)
        return cached_news

def get_dxy_tnx_bias():
    try:
        if not yf:
            return "NEUTRAL", "yf not available"
        dxy = yf.Ticker("DX-Y.NYB")
        hist_dxy = dxy.history(period="2d")
        if len(hist_dxy) < 2:
            return "NEUTRAL", "DXY no data"
        dxy_change = ((hist_dxy['Close'].iloc[-1] - hist_dxy['Close'].iloc[-2]) / hist_dxy['Close'].iloc[-2]) * 100

        tnx = yf.Ticker("^TNX")
        hist_tnx = tnx.history(period="2d")
        if len(hist_tnx) < 2:
            tnx_change = 0
        else:
            tnx_change = ((hist_tnx['Close'].iloc[-1] - hist_tnx['Close'].iloc[-2]) / hist_tnx['Close'].iloc[-2]) * 100

        if dxy_change < -0.30 and tnx_change < 0:
            return "BUY", f"DXY {dxy_change:.2f}% + US10Y {tnx_change:.2f}% -> Gold Bullish"
        elif dxy_change > 0.30 and tnx_change > 0:
            return "SELL", f"DXY {dxy_change:.2f}% + US10Y {tnx_change:.2f}% -> Gold Bearish"
        elif dxy_change < -0.20:
            return "BUY", f"DXY {dxy_change:.2f}% weak -> Gold Bullish"
        elif dxy_change > 0.20:
            return "SELL", f"DXY {dxy_change:.2f}% strong -> Gold Bearish"
        else:
            return "NEUTRAL", f"DXY {dxy_change:.2f}% + US10Y {tnx_change:.2f}% Neutral"
    except Exception as e:
        print(f"DXY fetch fail: {e}", flush=True)
        return "NEUTRAL", f"DXY error {e}"

def analyze_fundamental(pair="XAUUSD"):
    global last_fund_bias
    news = fetch_forexfactory_news()
    now = datetime.now(pytz.utc)
    
    for n in news:
        title = n.get("title","").lower()
        if not any(x in title for x in ["cpi","fomc","interest","nfp","nonfarm","gdp","ppi","retail"]):
            continue
        try:
            nt = datetime.fromisoformat(n["time"].replace("Z","+00:00"))
            if nt - timedelta(minutes=60) <= now <= nt + timedelta(minutes=60):
                return {
                    "pair": pair,
                    "block_type": "BLOCK",
                    "bias": "NEUTRAL",
                    "fund_bias": "NEUTRAL",
                    "alert_message": f"🔴 USD {n.get('title')} BLOCK 60m",
                    "reason": f"High impact {n.get('title')} in {int((nt-now).total_seconds()/60)}min",
                    "news": n.get('title')
                }
        except:
            continue

    dxy_bias, dxy_reason = get_dxy_tnx_bias()
    last_fund_bias = {"bias": dxy_bias, "reason": dxy_reason}

    if dxy_bias in ["BUY", "SELL"]:
        return {
            "pair": pair,
            "block_type": "CLEAR",
            "bias": dxy_bias,
            "fund_bias": dxy_bias,
            "alert_message": "",
            "reason": dxy_reason,
            "news": dxy_reason
        }
    
    return {
        "pair": pair,
        "block_type": "CLEAR",
        "bias": "NEUTRAL",
        "fund_bias": "NEUTRAL",
        "alert_message": "",
        "reason": dxy_reason,
        "news": None
    }

def is_news_block_active(pair="XAUUSD"):
    res = analyze_fundamental(pair)
    if res["block_type"] == "BLOCK":
        return True, res["alert_message"], res.get("news","")
    return False, "", ""
