# BOT 1: A+ SMC FULL - Top Down + Liquidity + SD + Fib + FVG + OB + News - ALL PAIRS

import datetime

# YOUR 10 PAIRS
PAIR_IMPACT = {
    "GBPUSD": ["USD", "GBP"],
    "GBPJPY": ["GBP", "JPY"],
    "XAUUSD": ["USD", "XAU"],
    "AUDCAD": ["AUD", "CAD"],
    "EURUSD": ["USD", "EUR"],
    "AUDUSD": ["USD", "AUD"],
    "USDJPY": ["USD", "JPY"],
    "BTCUSD": ["USD", "BTC"],
    "NAS100": ["USD", "US"],
    "SPX500": ["USD", "US"],
    "SPX": ["USD", "US"],
}

def ema(data, period):
    if len(data) < period: return sum(data)/len(data)
    return sum(data[-period:]) / period

def get_trend_structure(candles):
    if len(candles) < 60: return "NEUTRAL"
    closes = [c['close'] for c in candles]
    highs = [c['high'] for c in candles]
    lows = [c['low'] for c in candles]
    e50 = ema(closes, 50)
    e200 = ema(closes, 200)
    recent_high = max(highs[-20:-1])
    recent_low = min(lows[-20:-1])
    last_close = closes[-1]
    if last_close > e50 and e50 > e200 and last_close > recent_high:
        return "BULLISH"
    elif last_close < e50 and e50 < e200 and last_close < recent_low:
        return "BEARISH"
    return "NEUTRAL"

def check_fvg(candles):
    if len(candles) < 10: return False, "No FVG"
    for i in range(len(candles)-3, len(candles)-8, -1):
        c1, c2, c3 = candles[i-2], candles[i-1], candles[i]
        if c1['high'] < c3['low'] and (c3['low'] - c1['high']) > (c1['high']-c1['low'])*0.5:
            if abs(candles[-1]['close'] - c1['high']) < (c3['low']-c1['high'])*2:
                return True, f"Bullish FVG {c1['high']:.2f}-{c3['low']:.2f}"
        if c1['low'] > c3['high'] and (c1['low'] - c3['high']) > (c1['high']-c1['low'])*0.5:
            if abs(candles[-1]['close'] - c1['low']) < (c1['low']-c3['high'])*2:
                return True, f"Bearish FVG {c3['high']:.2f}-{c1['low']:.2f}"
    return False, "No valid FVG retest"

def check_order_block(candles, bias):
    if len(candles) < 30: return False, "No OB"
    last_close = candles[-1]['close']
    for i in range(len(candles)-5, len(candles)-30, -1):
        body = abs(candles[i]['close'] - candles[i]['open'])
        avg_body = sum([abs(c['close']-c['open']) for c in candles[i-10:i]]) / 10
        if body > avg_body * 2:
            ob_high = max(candles[i]['open'], candles[i]['close'])
            ob_low = min(candles[i]['open'], candles[i]['close'])
            if bias=="BULLISH" and ob_low <= last_close <= ob_high*1.005:
                return True, f"Bullish OB {ob_low:.2f}-{ob_high:.2f}"
            if bias=="BEARISH" and ob_high >= last_close >= ob_low*0.995:
                return True, f"Bearish OB {ob_low:.2f}-{ob_high:.2f}"
    return False, "No OB mitigation"

def check_liquidity_sweep(candles_4h, bias):
    if len(candles_4h) < 30: return False, "No sweep"
    recent_high = max([c['high'] for c in candles_4h[-20:-1]])
    recent_low = min([c['low'] for c in candles_4h[-20:-1]])
    last = candles_4h[-1]
    prev = candles_4h[-2]
    if bias == "BULLISH":
        if prev['low'] < recent_low and last['close'] > recent_low and last['close'] > prev['open']:
            return True, f"Swept Low {recent_low:.2f} -> Reclaim"
    else:
        if prev['high'] > recent_high and last['close'] < recent_high and last['close'] < prev['open']:
            return True, f"Swept High {recent_high:.2f} -> Reject"
    return False, "No sweep"

def check_fibonacci_ote(candles_1h, bias):
    if len(candles_1h) < 40: return False, "No data"
    lookback = candles_1h[-30:]
    swing_high = max([c['high'] for c in lookback])
    swing_low = min([c['low'] for c in lookback])
    last = candles_1h[-1]['close']
    range_size = swing_high - swing_low
    if range_size == 0: return False, "No range"
    eq = (swing_high+swing_low)/2
    if bias=="BULLISH":
        fib_62 = swing_high - range_size*0.62
        fib_79 = swing_high - range_size*0.79
        in_discount = last < eq
        in_ote = fib_79 <= last <= fib_62
        return (in_discount and in_ote), f"OTE {fib_79:.2f}-{fib_62:.2f} Discount:{in_discount}"
    else:
        fib_62 = swing_low + range_size*0.62
        fib_79 = swing_low + range_size*0.79
        in_premium = last > eq
        in_ote = fib_62 <= last <= fib_79
        return (in_premium and in_ote), f"OTE {fib_62:.2f}-{fib_79:.2f} Premium:{in_premium}"

def check_15m_smc(candles_15m, bias):
    if len(candles_15m) < 20: return False, "No data"
    last = candles_15m[-1]
    prev_high = max([c['high'] for c in candles_15m[-11:-1]])
    prev_low = min([c['low'] for c in candles_15m[-11:-1]])
    if bias=="BULLISH" and last['close'] > prev_high:
        return True, f"15M BOS Bullish {prev_high:.2f}"
    if bias=="BEARISH" and last['close'] < prev_low:
        return True, f"15M BOS Bearish {prev_low:.2f}"
    return False, "No 15M MSS"

def check_news_filter(pair="XAUUSD"):
    """NEWS FILTER FOR ALL 10 PAIRS"""
    now = datetime.datetime.utcnow()
    # Get news that affects this specific pair
    news_times = {
        "USD": [(12,30),(13,15),(14,0),(18,0)],
        "GBP": [(8,30)],
        "EUR": [(7,15),(12,45)],
        "AUD": [(1,30)],
        "CAD": [(12,30)],
        "JPY": [(23,50)],
        "BTC": [(15,0)],
        "US": [(13,30),(14,30)], # NAS/SPX
        "XAU": [(12,30),(14,0)]
    }
    currencies = PAIR_IMPACT.get(pair, ["USD"])
    for curr in currencies:
        for h,m in news_times.get(curr, []):
            if now.hour==h and abs(now.minute-m)<50:
                return False, f"NEWS BLOCK: {curr} news {h}:{m} GMT affects {pair}"
    return True, f"News Safe for {pair}"

def analyze_top_down(candles_1d, candles_4h, candles_1h, candles_15m, pair="XAUUSD"):
    bias = get_trend_structure(candles_1d)
    if bias=="NEUTRAL":
        return {"setup":False, "reason":"1D NEUTRAL"}

    sweep_ok, sweep_msg = check_liquidity_sweep(candles_4h, bias)
    ob_ok, ob_msg = check_order_block(candles_1h, bias)
    fvg_ok, fvg_msg = check_fvg(candles_1h)
    fib_ok, fib_msg = check_fibonacci_ote(candles_1h, bias)
    m15_ok, m15_msg = check_15m_smc(candles_15m, bias)
    news_ok, news_msg = check_news_filter(pair)

    sd_ok = ob_ok or fvg_ok
    is_a_plus = all([bias!="NEUTRAL", sweep_ok, sd_ok, fib_ok, m15_ok, news_ok])

    return {
        "setup": is_a_plus,
        "bias": bias,
        "final": bias if is_a_plus else "NO TRADE",
        "pair": pair,
        "checks": {
            "1D Bias": bias,
            "4H Sweep": sweep_ok,
            "OB": ob_ok,
            "FVG": fvg_ok,
            "Fib OTE": fib_ok,
            "15M BOS": m15_ok,
            "News": news_ok
        },
        "msgs": {
            "sweep": sweep_msg,
            "ob": ob_msg,
            "fvg": fvg_msg,
            "fib": fib_msg,
            "m15": m15_msg,
            "news": news_msg
        }
                }
