import time
from flask import Flask
import threading
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Kobbyforex Bot is LIVE! 🚀"

def run_bot():
    print("="*40)
    print("🚀 Kobbyforex Bot Started!")
    print("="*40)
    while True:
        print("✅ Kobbyforex Bot is LIVE! Waiting for strategy...")
        time.sleep(60)  # Check every 60 seconds

# Run Flask for Render/UptimeRobot
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # Start bot in background
    threading.Thread(target=run_bot, daemon=True).start()
    # Start Flask
    run_flask()
