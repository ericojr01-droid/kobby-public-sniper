import time
import requests
from flask import Flask
import threading
import os
from datetime import datetime
import pytz

from bots.top_down import analyze_top_down
from bots.fundamental import analyze_fundamental
from bots.entry_risk import generate_entry
from bots.market_status import is_trading_allowed, get_market_status_alert, is_forex_market_open

BOT_TOKEN = "8826207602:AAEnJMlJOb6lW1QHV4aJ9E8edPacTprTE_Q"
CHAT_ID = "8240862120"
CHANNEL_ID = "@KobbyforexTrade"

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data1 = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, data=data1, timeout=10)
        data2 = {"chat_id": CHANNEL_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, data=data2, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

app = Flask(__name__)

PAIRS = ["GBPUSD","GBPJPY","XAUUSD","AUDCAD","EURUSD","AUDUSD","USDJPY","BTCUSD","NAS100","SPX500"]

@app.route('/')
def home():
    return "Kobbyforex Bot is LIVE! 🚀 10 Pairs Scanning 24/7 | @KobbyforexTrade"

def run_bot():
    print("="*40)
    print("🚀 Kobbyforex Bot Started!")
    print("="*40)
    send_telegram("🚀 <b>Kobbyforex Bot is LIVE 24/7!</b>\n\n✅ 10 Pairs Scanning\n✅ BOT1 Top Down SMC\n✅ BOT2 News Filter\n✅ BOT3 Entry 1% + 3TPs\n✅ BOT4 Market Status\n\n📢 Channel: @KobbyforexTrade")
    
    while True:
        try:
            # Hourly status
            if datetime.now().minute == 0:
                try:
                    status = get_market_status_alert()
                    if not is_forex_market_open():
                        send_telegram(status["full_message"])
                except:
                    pass

            for pair in PAIRS:
                if not is_trading_allowed(pair):
                    continue

                fund = analyze_fundamental(pair)
                if not fund["allow_trading"]:
                    send_telegram(fund["alert_message"])
                    continue

                if fund["block_type"] == "WARNING":
                    send_telegram(fund["alert_message"])

                tech = analyze_top_down(pair)
                if not tech.get("setup"):
                    continue

                bias = tech["bias"]
                entry_price = tech["entry_price"]
                source = tech.get("source", "TECHNICAL")
                
                entry_data = generate_entry(pair, bias, entry_price, source, balance=1000)
                
                if entry_data:
                    extra = tech.get("confluence","")
                    msg = f"{entry_data['alert_message']}\n\n📊 {extra}\n⏰ {datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M UTC')}"
                    send_telegram(msg)
                
                time.sleep(2)

            print("✅ Kobbyforex Bot is LIVE! Waiting for strategy...")
            time.sleep(300)  # Scan every 5 mins

        except Exception as e:
            print(f"Main error: {e}")
            time.sleep(60)

# Run Flask for Render/UptimeRobot
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    run_flask()
