import time
import os
import requests
import threading
from datetime import datetime
from flask import Flask
from bots.top_down import analyze_top_down
from bots.fundamental import analyze_fundamental
from bots.entry_risk import generate_entry
from bots.market_status import check_session_status

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")
BALANCE = float(os.getenv("BALANCE", "1000"))

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        for cid in [CHAT_ID, CHANNEL_ID]:
            if cid:
                requests.post(url, data={"chat_id": cid, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"TG error {e}", flush=True)

def run_scan():
    print(f"=== SCAN START {datetime.utcnow().strftime('%H:%M:%S')} ===", flush=True)
    active, _ = check_session_status()
    print(f"Active: {active}", flush=True)
    fund = analyze_fundamental("XAUUSD")
    if fund["block_type"] == "BLOCK":
        print("BLOCKED", flush=True)
        return
    top = analyze_top_down("XAUUSD")
    if not top["setup"]:
        print(f"No setup: {top.get('reason')}", flush=True)
        return
    entry = generate_entry("XAUUSD", top["bias"], top["entry_price"], top["stop_loss"], BALANCE, 1, top["source"])
    if not entry:
        print("Entry calc fail", flush=True)
        return
    msg = f"{entry['alert_message']}\n\n<b>{top['strength']}</b>\n{top['confluence']}"
    send_telegram(msg)
    print(f"SIGNAL SENT {top['bias']}", flush=True)

def bot_loop():
    print("BOT LOOP STARTED", flush=True)
    send_telegram("🤖 KOBBYFOREX LIVE - XAUUSD ONLY - FINAL")
    while True:
        try:
            run_scan()
        except Exception as e:
            print(f"Loop error {e}", flush=True)
        time.sleep(900)

threading.Thread(target=bot_loop, daemon=True).start()

@app.route("/")
def home():
    return "KOBBYFOREX XAUUSD RUNNING"

@app.route("/health")
def health():
    return "OK"
