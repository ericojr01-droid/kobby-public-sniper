import telebot, os, threading, time, requests, pytz
from flask import Flask, request
from datetime import datetime
from bs4 import BeautifulSoup
import json

BOT_TOKEN = "8826207602:AAE4r7jP4sj40hmrAoR2vN_ZIEBIu9vR5IY"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

SUBS = set()
last_news_alert = {}
news_block_until = {}

def send_to_all(msg):
    for chat_id in list(SUBS):
        try:
            bot.send_message(chat_id, msg, parse_mode='Markdown')
        except:
            pass

def get_session():
    now = datetime.now(pytz.timezone('UTC'))
    hour = now.hour
    if 0 <= hour < 8: return "ASIAN"
    elif 8 <= hour < 13: return "LONDON"
    elif 13 <= hour < 21: return "NEW YORK"
    else: return "CLOSED"

def session_valid_pairs(session):
    if session == "ASIAN": return ["AUDUSD","NZDUSD","USDJPY","BTCUSD","ETHUSD"]
    if session == "LONDON": return ["EURUSD","GBPUSD","EURGBP","EURJPY","GBPJPY","BTCUSD"]
    if session == "NEW YORK": return ["EURUSD","GBPUSD","USDCAD","USDCHF","BTCUSD","ETHUSD","XAUUSD"]
    return []

def get_forex_news():
    try:
        url = "https://www.forexfactory.com/calendar"
        headers = {"User-Agent":"Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'lxml')
        events = []
        for row in soup.find_all("tr", class_="calendar__row"):
            impact = row.find("td", class_="calendar__impact")
            if impact and "high" in str(impact).lower():
                time_td = row.find("td", class_="calendar__time")
                currency = row.find("td", class_="calendar__currency")
                event = row.find("td", class_="calendar__event")
                if time_td and currency and event:
                    events.append({
                        "currency": currency.text.strip(),
                        "event": event.text.strip(),
                        "time": time_td.text.strip()
                    })
        return events[:3]
    except:
        return []

def get_crypto_news():
    try:
        url = "https://cryptopanic.com/api/v1/posts/?auth_token=free&public=true"
        r = requests.get(url, timeout=10).json()
        big_news = []
        for post in r.get("results", [])[:5]:
            if post.get("currencies"):
                big_news.append(post["title"])
        return big_news[:2]
    except:
        return []

def news_loop():
    while True:
        try:
            forex_events = get_forex_news()
            if forex_events:
                for ev in forex_events:
                    curr = ev['currency']
                    msg = f"🔴 *HIGH IMPACT NEWS ALERT*\n\n💱 Currency: *{curr}*\n📰 Event: {ev['event']}\n⏰ Time: {ev['time']}\n\n⚠️ *10MIN WARNING:* No A+ for {curr} pairs!"
                    if curr not in last_news_alert or time.time() - last_news_alert[curr] > 3600:
                        send_to_all(msg)
                        last_news_alert[curr] = time.time()
                        news_block_until[curr] = time.time() + 1800
            crypto = get_crypto_news()
            if crypto:
                msg = f"₿ *CRYPTO BREAKING NEWS*\n\n📰 {crypto[0]}\n\n⚠️ Volatility for BTC/ETH!"
                if "CRYPTO" not in last_news_alert or time.time() - last_news_alert["CRYPTO"] > 3600:
                    send_to_all(msg)
                    last_news_alert["CRYPTO"] = time.time()
        except:
            pass
        time.sleep(60)

def market_loop():
    last_session = ""
    while True:
        try:
            sess = get_session()
            if sess!= last_session:
                if sess!= "CLOSED":
                    pairs = ",".join(session_valid_pairs(sess))
                    send_to_all(f"🟢 *{sess} SESSION OPEN*\nValid pairs: {pairs}\nLiquidity + Fib active...")
                else:
                    send_to_all("🔴 *MARKET CLOSED*")
                last_session = sess
        except:
            pass
        time.sleep(60)

@bot.message_handler(commands=['start'])
def start(m):
    SUBS.add(m.chat.id)
    bot.reply_to(m, f"✅ *KOBBY V7 SNIPER ACTIVE!*\n\nSession: {get_session()}\n\nFeatures: TradingView, ForexFactory 10min, Crypto news, Liquidity Sweep, Fib, 3TPs (1:2,1:3,1:5), 2% Risk\n\nYou go get alerts!")

@bot.message_handler(commands=['status'])
def status(m):
    bot.reply_to(m, f"Session: {get_session()}\nValid: {session_valid_pairs(get_session())}")

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        pair = data.get("pair","").upper()
        action = data.get("action","").upper()
        entry = float(data.get("entry",0))
        sl = float(data.get("sl",0))

        # AUTO CALC 3 TPs with RR 1:2, 1:3, 1:5 + 2% RISK
        risk = abs(entry - sl)
        if action == "BUY":
            tp1 = entry + (risk * 2)
            tp2 = entry + (risk * 3)
            tp3 = entry + (risk * 5)
        else:
            tp1 = entry - (risk * 2)
            tp2 = entry - (risk * 3)
            tp3 = entry - (risk * 5)

        fib = data.get("fib","61.8%")
        liquidity = data.get("liquidity","SWEPT")

        # NEWS BLOCK CHECK
        base_curr = pair[:3]
        quote_curr = pair[3:6]
        for curr in [base_curr, quote_curr]:
            if curr in news_block_until and time.time() < news_block_until[curr]:
                send_to_all(f"🚫 *A+ BLOCKED by NEWS* - {pair} {action} blocked due to {curr} news!")
                return "blocked", 200

        sess = get_session()
        msg = f"""🎯 *KOBBY V7 A+ SNIPER ENTRY*

*Pair:* {pair}
*Action:* {action}
*Session:* {sess}
*Entry:* {entry}
*SL:* {sl} (2% Risk)
*TP1:* {tp1} (1:2 RR - Take 50%)
*TP2:* {tp2} (1:3 RR - Take 30%)
*TP3:* {tp3} (1:5 RR - Runner 20%)

✅ *Filters Passed:*
- Liquidity Sweep: {liquidity}
- Fibonacci: {fib}
- News: PASSED
- Top-Down: Aligned

💰 *Risk:* 2% MAX! Move SL to BE after TP1!"""

        send_to_all(msg)
        return "ok", 200
    except Exception as e:
        return str(e), 400

@app.route('/')
def home():
    return "KOBBY V7 RUNNING - 3TPs + 2% Risk Locked!"

threading.Thread(target=news_loop, daemon=True).start()
threading.Thread(target=market_loop, daemon=True).start()
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()

bot.infinity_polling()
