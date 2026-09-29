import time
import os
import requests
import threading
from datetime import datetime
from flask import Flask

from bots.top_down import analyze_top_down
from bots.fundamental import analyze_fundamental
from bots.entry_risk import generate_entry
from bots.market_status import (
    check_session_status,
    should_send_session_alert,
    should_send_market_open_close_alert,
    get_session_status_message,
    is_forex_market_open
)

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"text": msg, "parse_mode": "HTML"}
        sent = False
        for cid in [CHANNEL_ID, CHAT_ID]:
            if not cid:
                continue
            try:
                r = requests.post(f"{url}", data={**payload, "chat_id": cid}, timeout=12)
                if r.status_code == 200:
                    sent = True
            except Exception as e:
                print(f"TG send to {cid} fail {e}", flush=True)
        return sent
    except Exception as e:
        print(f"TG error {e}", flush=True)
        return False

def run_scan():
    print(f"=== SCAN {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC ===", flush=True)

    # 1. Market open/close - SEND ONLY ON CHANGE
    should_send_mc, mc_type = should_send_market_open_close_alert()
    if should_send_mc:
        if mc_type == "OPEN":
            send_telegram("🟢 <b>FOREX MARKET OPEN</b> - XAUUSD SCAN STARTED")
            print("MARKET OPEN alert sent", flush=True)
        elif mc_type == "CLOSE":
            send_telegram("🔴 <b>FOREX MARKET CLOSED</b> - See you Sunday 22:00 GMT")
            print("MARKET CLOSE alert sent", flush=True)

    # If market closed, stop here
    if not is_forex_market_open():
        print("Market closed - skip", flush=True)
        return

    # 2. Session open - SEND ONLY WHEN NEW SESSION STARTS
    should_send_sess, new_sessions = should_send_session_alert()
    if should_send_sess and new_sessions:
        msg = get_session_status_message(new_sessions)
        if msg:
            send_telegram(f"{msg}\n\nXAUUSD scan active")
            print(f"SESSION OPEN {new_sessions} sent", flush=True)

    # 3. Fundamental check - CAN GIVE OWN ENTRY + BLOCK
    fund = analyze_fundamental("XAUUSD")
    print(f"FUND: {fund.get('fund_bias')} | {fund.get('reason')} | {fund.get('block_type')}", flush=True)

    if fund["block_type"] == "BLOCK":
        print(f"BLOCKED by {fund.get('news')}", flush=True)
        return

    # Fundamental entry (if strong DXY bias)
    if fund.get("fund_bias") in ["BUY", "SELL"]:
        # Need current price for fundamental entry
        top_for_price = analyze_top_down("XAUUSD")
        if top_for_price and top_for_price.get("entry_price"):
            curr_price = top_for_price["entry_price"]
            sl_price = top_for_price.get("stop_loss", curr_price - 5 if fund["fund_bias"] == "BUY" else curr_price + 5)
            f_entry = generate_entry("XAUUSD", fund["fund_bias"], curr_price, sl_price, f"FUNDAMENTAL: {fund['reason']}")
            if f_entry:
                # Only send fundamental if no technical setup this cycle (to avoid double)
                pass  # will be handled below with confluence check

    # 4. Technical Top-Down
    top = analyze_top_down("XAUUSD")
    if not top.get("setup"):
        print(f"No technical setup: {top.get('reason')}", flush=True)
        # If no tech but fund is strong, send fund only
        if fund.get("fund_bias") in ["BUY", "SELL"] and top.get("entry_price"):
            curr_price = top["entry_price"]
            sl_price = top.get("stop_loss", curr_price - 5 if fund["fund_bias"] == "BUY" else curr_price + 5)
            f_entry = generate_entry("XAUUSD", fund["fund_bias"], curr_price, sl_price, f"FUNDAMENTAL: {fund['reason']}")
            if f_entry:
                msg = (
                    f"🔶 <b>FUNDAMENTAL {fund['fund_bias']} XAUUSD</b>\n\n"
                    f"{f_entry['alert_message']}\n\n"
                    f"<b>{fund['reason']}</b>"
                )
                send_telegram(msg)
                print(f"FUND SIGNAL SENT {fund['fund_bias']}", flush=True)
        return

    # 5. Generate Entry
    entry = generate_entry("XAUUSD", top["bias"], top["entry_price"], top["stop_loss"], top.get("confluence", top["source"]))
    if not entry:
        print("Entry calc fail", flush=True)
        return

    # 6. Check confluence with fundamental
    is_confluence = fund.get("fund_bias") == top["bias"]

    if is_confluence:
        msg = (
            f"🔥🔥 <b>STRONG CONFLUENCE {top['bias']} XAUUSD</b> 🔥🔥\n\n"
            f"{entry['alert_message']}\n\n"
            f"<b>TECH:</b> {top['confluence']}\n"
            f"<b>FUND:</b> {fund['reason']}\n\n"
            f"<b>{top['strength']} SETUP</b>"
        )
    else:
        msg = (
            f"🔷 <b>TECHNICAL {top['bias']} XAUUSD</b>\n\n"
            f"{entry['alert_message']}\n\n"
            f"<b>{top['confluence']}</b>\n"
            f"FUND: {fund.get('reason')}\n\n"
            f"<b>{top['strength']}</b>"
        )

    send_telegram(msg)
    print(f"TECH SIGNAL SENT {top['bias']} Confluence={is_confluence}", flush=True)

def bot_loop():
    print("BOT LOOP STARTED - XAUUSD ONLY", flush=True)
    send_telegram("🤖 <b>KOBBYFOREX LIVE</b>\nXAUUSD ONLY | SMC 4H→1H→15M + ForexFactory + DXY\nSession alerts: OPEN only | Market: OPEN/CLOSE only")
    while True:
        try:
            run_scan()
        except Exception as e:
            print(f"Loop error {e}", flush=True)
            import traceback
            traceback.print_exc()
        time.sleep(900)

threading.Thread(target=bot_loop, daemon=True).start()

@app.route("/")
def home():
    active, _ = check_session_status()
    is_open = is_forex_market_open()
    return f"KOBBYFOREX XAUUSD RUNNING | Market: {'OPEN' if is_open else 'CLOSED'} | Active: {active}"

@app.route("/health")
def health():
    return "OK"

@app.route("/scan")
def manual_scan():
    threading.Thread(target=run_scan, daemon=True).start()
    return "Scan triggered"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
