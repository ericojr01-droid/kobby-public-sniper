import time, os, requests
from datetime import datetime
from bots.top_down import analyze_top_down
from bots.fundamental import analyze_fundamental
from bots.entry_risk import generate_entry
from bots.market_status import check_session_status, is_forex_market_open

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")
BALANCE = float(os.getenv("BALANCE", "1000"))
PAIRS = ["XAUUSD"]

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        for cid in [CHAT_ID, CHANNEL_ID]:
            if cid:
                requests.post(url, data={"chat_id": cid, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except: pass

def run_scan():
    print(f"\n=== SCAN START {datetime.utcnow().strftime('%H:%M:%S GMT')} ===", flush=True)
    active,_ = check_session_status()
    print(f"Active Sessions: {active} | Forex Open: {is_forex_market_open()}", flush=True)
    for pair in PAIRS:
        fund = analyze_fundamental(pair)
        if fund["block_type"] == "BLOCK":
            print(f"🔴 {pair} BLOCKED: {fund['alert_message']}", flush=True)
            continue
        print(f"Checking {pair}...", flush=True)
        top = analyze_top_down(pair)
        if not top["setup"]:
            print(f"❌ {pair}: {top.get('reason','No setup')}", flush=True)
            continue
        entry_data = generate_entry(pair, top["bias"], top["entry_price"], top["stop_loss"], BALANCE, 1, top["source"])
        if not entry_data:
            print(f"❌ {pair}: Entry calc fail", flush=True)
            continue
        msg = f"{entry_data['alert_message']}\n\n<b>{top['strength']}</b>\n{top['confluence']}\nFundamental: {fund['block_type']} ✅"
        send_telegram(msg)
        print(f"✅ SIGNAL SENT {pair} {top['bias']}", flush=True)
    print("=== SCAN END ===\n", flush=True)

if __name__ == "__main__":
    send_telegram("🤖 KOBBYFOREX V2 LIVE - XAUUSD ONLY - Pure SMC - 15min")
    while True:
        try: run_scan()
        except Exception as e: print(f"Loop Error: {e}", flush=True)
        time.sleep(900)
