import telebot, yfinance as yf, requests, time, json, os
from flask import Flask, request
import threading
from datetime import datetime

BOT_TOKEN = "8826207602:AAE4r7jP4sj40hmrAoR2vN_ZIEBIu9vR5IY"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

PAIRS = ["BTCUSD","GBPJPY","EURUSD","AUDUSD","AUDCAD","XAUUSD","SPX","NAS100","ETHUSD","AUDNZD"]
SUBS_FILE = "subs.json"

def load_subs():
    if os.path.exists(SUBS_FILE):
        with open(SUBS_FILE, 'r') as f: return json.load(f)
    return []

def save_subs(subs):
    with open(SUBS_FILE, 'w') as f: json.dump(subs, f)

def broadcast(text):
    subs = load_subs()
    for uid in subs:
        try: bot.send_message(uid, text, parse_mode="Markdown")
        except: pass

@bot.message_handler(commands=['start'])
def start(m):
    subs = load_subs()
    if m.chat.id not in subs:
        subs.append(m.chat.id)
        save_subs(subs)
    bot.reply_to(m, f"""🔥 *KOBBYFOREX A+ PUBLIC SNIPER LIVE* 🔥

Welcome {m.from_user.first_name}!

I dey scan 24/7 for A+ setups only:
{', '.join(PAIRS)}

✅ Top-Down 1D-4H-1H-15M
✅ SMC Liquidity Sweep + Supply/Demand
✅ News Filter
✅ TP1 1:2 | TP2 1:3 | TP3 1:5

You go get alert ONLY when A+ happen - no spam!

Commands:
/pairs - see pairs
/status - bot status
""", parse_mode="Markdown")

@bot.message_handler(commands=['pairs'])
def pairs_cmd(m): 
    bot.reply_to(m, "📊 Pairs: " + ", ".join(PAIRS) + "\n24/7 Crypto Hours")

@bot.message_handler(commands=['status'])
def status(m): 
    bot.reply_to(m, f"🟢 ONLINE 24/7 - Scanning {len(PAIRS)} pairs every 15min")

# WEBHOOK FOR TRADINGVIEW
@app.route('/webhook', methods=['POST'])
def webhook():
    d = request.json
    pair = d.get('pair')
    action = d.get('action')
    entry = float(d.get('entry'))
    sl = float(d.get('sl'))
    risk = abs(entry-sl)
    tp1 = entry+risk*2 if action=="BUY" else entry-risk*2
    tp2 = entry+risk*3 if action=="BUY" else entry-risk*3
    tp3 = entry+risk*5 if action=="BUY" else entry-risk*5
    
    msg = f"""🎯 *A+ PUBLIC SIGNAL* 🎯
Pair: {pair} | {action} @ {entry}
SL: {sl}
TP1 1:2 {tp1:.2f} | TP2 1:3 {tp2:.2f} | TP3 1:5 {tp3:.2f}
TopDown + SMC + News ✅
"""
    broadcast(msg)
    return "OK", 200

@app.route('/')
def home(): 
    return "KOBBY PUBLIC BOT LIVE 24/7"

def bot_polling():
    bot.polling(none_stop=True)

threading.Thread(target=bot_polling, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
