import os
import time
import threading
import requests
from flask import Flask

BOT_TOKEN = "8826207602:AAEnJMlJOb6lW1QHV4aJ9E8edPacTprTE_Q"
CHANNEL_ID = "@KobbyforexTrade"

# Import your existing logic from bots folder
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

def bot_loop():
    print("Bot loop started...")
    send_telegram("✅ KobbyForex Bot is LIVE on Render")
    while True:
        try:
            if not is_market_open():
                print("Market closed, waiting...")
                time.sleep(300)
                continue

            if not check_fundamentals():
                print("High impact news, skipping...")
                time.sleep(300)
                continue

            result = analyze_top_down()
            
            if result and result.get("signal"):
                entry_data = check_entry(result)
                if entry_data and entry_data.get("valid"):
                    msg = entry_data.get("message", str(result))
                    send_telegram(msg)
            
            time.sleep(120)

        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(60)

@app.route('/')
def home():
    return "✅ KobbyForex Bot is LIVE", 200

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    threading.Thread(target=bot_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
