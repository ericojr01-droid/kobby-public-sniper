import os
import time
import threading
import requests
from flask import Flask

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8826270602:AAEnJMLJOb6lW1QH4VaJ9E8edPacTprTE_Q")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@KobbyforexTrade")

# Safe imports - no go crash if name different
from bots.top_down import analyze_top_down
from bots import entry_risk
from bots.fundamental import check_fundamentals
from bots.market_status import is_market_open

app = Flask(__name__)

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHANNEL_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_entry_signal():
    # Try all possible function names inside entry_risk.py
    for name in ["check_entry", "check_risk", "analyze_entry", "entry_check", "get_signal"]:
        if hasattr(entry_risk, name):
            return getattr(entry_risk, name)()
    # If no function found, return file doc
    return f"entry_risk loaded: {dir(entry_risk)}"

def bot_loop():
    print("Bot loop started...")
    send_telegram("✅ KobbyForex Bot is LIVE on Render - Fixed version")
    while True:
        try:
            if is_market_open():
                top = analyze_top_down()
                fund = check_fundamentals()
                entry = get_entry_signal()
                print(f"Checked: {top} | {fund} | {entry}")
            else:
                print("Market closed")
            time.sleep(300)
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(60)

threading.Thread(target=bot_loop, daemon=True).start()

@app.route('/')
def home():
    return "KobbyForex Bot Running - LIVE"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
