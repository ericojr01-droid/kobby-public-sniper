import os
import time
import threading
import requests
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")

from bots.top_down import analyze_top_down
from bots.fundamental import analyze_fundamental
from bots.entry_risk import generate_entry
from bots.market_status import get_market_status_alert, is_trading_allowed

app = Flask(__name__)

PAIRS = ["GBPUSD","GBPJPY","XAUUSD","AUDCAD","EURUSD","AUDUSD","USDJPY","BTCUSD","NAS100","SPX500"]
BALANCE = 1000  # Change to your account balance

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        for cid in [CHAT_ID, CHANNEL_ID]:
            if cid:
                data = {"chat_id": cid, "text": message, "parse_mode": "HTML"}
                requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")


                    
                            def bot_loop():
    print("KobbyForex Loop Started")
    # send_telegram REMOVED - no more alive message
    last_market_alert = 0

    while True:
        try:
            if time.time() - last_market_alert > 3600:
                market_data = get_market_status_alert()
                send_telegram(market_data["full_message"])
                last_market_alert = time.time()

            for pair in PAIRS:
                if not is_trading_allowed(pair):
                    continue

                fund = analyze_fundamental(pair)
                if not fund["allow_trading"]:
                    send_telegram(fund["alert_message"])
                    continue
                if fund["block_type"] == "WARNING":
                    send_telegram(fund["alert_message"])

                top = analyze_top_down(pair)
                if top.get("setup"):
                    entry_data = generate_entry(
                        pair=pair,
                        bias=top["bias"],
                        current_price=top["entry_price"],
                        source=top["source"],
                        balance=BALANCE
                    )
                    if entry_data:
                        msg = (
                            f"{top.get('strength','')}\n"
                            f"{entry_data['alert_message']}\n\n"
                            f"📍 {top['confluence']}\n"
                            f"📍 POI: {top['poi']}"
                        )
                        send_telegram(msg)

                time.sleep(10)

            time.sleep(300)

        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(60)

threading.Thread(target=bot_loop, daemon=True).start()

@app.route('/')
def home():
    return "KobbyForex Bot Running - 10 Pairs LIVE"

@app.route('/status')
def status():
    return {"status":"running", "pairs":PAIRS}

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
