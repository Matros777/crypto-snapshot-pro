"""
Crypto Snapshot Pro — x402 Agent for Agentic.Market
Agent ID: #3613
Service: Professional Multi-Factor Market Analysis ($0.025 per request)
"""
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
import httpx
import time
import base64
import json
from typing import Tuple

app = FastAPI(title="Crypto Snapshot Pro x402 Agent")

BINANCE_API = "https://api.binance.com/api/v3"
_cache = {}
_CACHE_TTL = 30


class AgentResponse(BaseModel):
    message: dict


# ============================================================
# x402 PAYMENT CONFIG — СТРОГИЙ
# ============================================================
PAYMENT_CONFIG = {
    "x402Version": 2,
    "resource": {
        "url": "https://crypto-snapshot-pro.onrender.com",
        "description": "Real-time crypto market analysis using 8-factor scoring: RSI, EMA(20/50), Volume Ratio, Bollinger Bands, RSI Divergence, ATR volatility, Pivot Points. Outputs: LONG/SHORT/HOLD signal, conviction level, Entry/Target/Stop. Price: $0.025 per request.",
        "mimeType": "application/json"
    },
    "accepts": [
        {
            "scheme": "exact",
            "network": "eip155:8453",
            "amount": "25000",
            "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "payTo": "0x5b7efd37546d6BB02463339cEaDdD80997aC97B3",
            "maxTimeoutSeconds": 300,
            "extra": {"name": "USD Coin", "version": "2"}
        }
    ]
}


def create_402_response():
    envelope = json.dumps(PAYMENT_CONFIG)
    encoded = base64.b64encode(envelope.encode("utf-8")).decode("utf-8")
    return Response(
        content="Payment Required",
        status_code=402,
        headers={"payment-required": encoded}
    )


def has_valid_payment(request: Request) -> bool:
    h = request.headers
    return bool(h.get("x-payment") or h.get("payment-signature") or h.get("authorization"))


# ====================== ПОЛНЫЙ АНАЛИЗ ======================
def calculate_rsi(closes: list[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(diff if diff >= 0 else 0)
        losses.append(0 if diff >= 0 else abs(diff))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)


def calculate_ema(prices: list[float], period: int) -> float:
    if not prices:
        return 0.0
    multiplier = 2 / (period + 1)
    ema = prices[0]
    for price in prices[1:]:
        ema = (price - ema) * multiplier + ema
    return round(ema, 2)


def calculate_macd(closes: list[float]) -> Tuple[float, float, float]:
    if len(closes) < 26:
        return 0.0, 0.0, 0.0
    ema12 = calculate_ema(closes, 12)
    ema26 = calculate_ema(closes, 26)
    macd = ema12 - ema26
    signal = calculate_ema([macd], 9) if len([macd]) >= 9 else macd
    histogram = macd - signal
    return round(macd, 2), round(signal, 2), round(histogram, 2)


def calculate_bollinger_bands(closes: list[float], period: int = 20, std_dev: float = 2):
    if len(closes) < period:
        return 0.0, 0.0, 0.0
    recent = closes[-period:]
    middle = sum(recent) / period
    std = (sum((x - middle) ** 2 for x in recent) / period) ** 0.5
    return round(middle + std_dev * std, 2), round(middle, 2), round(middle - std_dev * std, 2)


def detect_rsi_divergence(rsi: float, closes: list[float]) -> str:
    if len(closes) < 10:
        return 'none'
    recent = closes[-10:]
    trend = recent[-1] - recent[0]
    if trend < 0 and rsi > 50:
        return 'bullish'
    elif trend > 0 and rsi < 50:
        return 'bearish'
    return 'none'


def calculate_pivot_points(high: float, low: float, close: float) -> dict:
    pivot = (high + low + close) / 3
    return {
        'pivot': round(pivot, 2),
        'r1': round(2 * pivot - low, 2),
        's1': round(2 * pivot - high, 2),
        'r2': round(pivot + (high - low), 2),
        's2': round(pivot - (high - low), 2)
    }


def get_signal_from_factors(rsi, ema20, ema50, volume_ratio, high_low_range, macd, macd_signal, macd_hist, bb_upper, bb_middle, bb_lower, rsi_div, pivot):
    long_score = short_score = 0
    if rsi < 30: long_score += 2
    elif rsi > 70: short_score += 2
    elif rsi < 40: long_score += 1
    elif rsi > 60: short_score += 1

    if ema20 > ema50: long_score += 1
    else: short_score += 1

    if macd > macd_signal and macd_hist > 0: long_score += 1
    elif macd < macd_signal and macd_hist < 0: short_score += 1

    if bb_upper and bb_lower:
        pos = (bb_middle - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
        if pos < 0.2: long_score += 1
        elif pos > 0.8: short_score += 1

    if volume_ratio > 1.5:
        if long_score > short_score: long_score += 1
        else: short_score += 1

    if rsi_div == 'bullish': long_score += 1
    elif rsi_div == 'bearish': short_score += 1

    if high_low_range > 0.03:
        if long_score > short_score: long_score += 1
        else: short_score += 1

    if long_score >= 4:
        return "LONG", "🚀 Strong Bullish Setup", long_score, short_score
    elif short_score >= 4:
        return "SHORT", "🔥 Strong Bearish Setup", long_score, short_score
    elif long_score > short_score:
        return "LONG", "⚡ Mild Bullish Bias", long_score, short_score
    elif short_score > long_score:
        return "SHORT", "⚠️ Mild Bearish Bias", long_score, short_score
    return "HOLD", "➡️ Neutral — Wait for Setup", long_score, short_score


def format_price(price: float) -> str:
    if price >= 1000:
        return f"${price:,.2f}"
    elif price >= 1:
        return f"${price:.2f}"
    return f"${price:.4f}"


async def fetch_ticker(symbol: str):
    cache_key = f"t_{symbol}"
    now = time.time()
    if cache_key in _cache and now - _cache[cache_key]["time"] < _CACHE_TTL:
        return _cache[cache_key]["data"]
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{BINANCE_API}/ticker/24hr", params={"symbol": symbol})
        data = r.json()
        _cache[cache_key] = {"data": data, "time": now}
        return data


async def fetch_klines(symbol: str):
    cache_key = f"k_{symbol}"
    now = time.time()
    if cache_key in _cache and now - _cache[cache_key]["time"] < _CACHE_TTL:
        return _cache[cache_key]["data"]
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{BINANCE_API}/klines", params={"symbol": symbol, "interval": "1d", "limit": 50})
        data = r.json()
        klines = [{"close": float(k[4]), "high": float(k[2]), "low": float(k[3]), "volume": float(k[5])} for k in data]
        _cache[cache_key] = {"data": klines, "time": now}
        return klines


# ============================================================
# MAIN ENDPOINT
# ============================================================
@app.api_route("/", methods=["GET", "POST"])
async def crypto_snapshot(request: Request):
    if not has_valid_payment(request):
        return create_402_response()

    symbol = "ETH"
    if request.method == "POST":
        try:
            body = await request.json()
            symbol = body.get("symbol", symbol)
        except:
            pass
    else:
        symbol = request.query_params.get("symbol", symbol)

    try:
        ticker = await fetch_ticker(symbol)
        current_price = float(ticker.get("lastPrice", 0))
        change_24h = float(ticker.get("priceChangePercent", 0))
        high_24h = float(ticker.get("highPrice", 0))
        low_24h = float(ticker.get("lowPrice", 0))

        klines = await fetch_klines(symbol)
        closes = [k["close"] for k in klines]
        volumes = [k["volume"] for k in klines]

        rsi = calculate_rsi(closes)
        ema20 = calculate_ema(closes[-20:], 20) if len(closes) >= 20 else current_price
        ema50 = calculate_ema(closes[-50:], 50) if len(closes) >= 50 else current_price
        avg_vol = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else volumes[-1] if volumes else 1
        volume_ratio = volumes[-1] / avg_vol if avg_vol > 0 else 1.0
        high_low_range = (high_24h - low_24h) / low_24h if low_24h > 0 else 0

        macd, macd_signal, macd_hist = calculate_macd(closes)
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(closes)
        rsi_div = detect_rsi_divergence(rsi, closes)
        pivot = calculate_pivot_points(high_24h, low_24h, current_price)

        signal, desc, long_s, short_s = get_signal_from_factors(
            rsi, ema20, ema50, volume_ratio, high_low_range,
            macd, macd_signal, macd_hist, bb_upper, bb_middle, bb_lower, rsi_div, pivot
        )

        # Расчёт уровней
        atr_proxy = high_low_range * current_price
        if signal == "LONG":
            entry = low_24h + (high_24h - low_24h) * 0.2
            target = entry + (entry - low_24h) * 2
            stop = low_24h - atr_proxy * 0.5
        elif signal == "SHORT":
            entry = high_24h - (high_24h - low_24h) * 0.2
            target = entry - (high_24h - entry) * 2
            stop = high_24h + atr_proxy * 0.5
        else:
            entry = target = stop = current_price

        risk_reward = abs((target - entry) / (entry - stop)) if entry != stop else 1.0

        total_score = long_s + short_s
        conviction = "VERY HIGH" if total_score >= 5 else "HIGH" if total_score >= 4 else "MEDIUM" if total_score >= 3 else "LOW"

        result = f"""📊 CRYPTO SNAPSHOT PRO — {symbol.replace('USDT', '/USDT')}
{desc}
📊 Conviction: {conviction}
🎯 Score: {long_s} LONG / {short_s} SHORT
💡 Reason: {'Bullish factors dominate.' if long_s > short_s else 'Bearish factors dominate.' if short_s > long_s else 'Mixed signals.'}

📈 TECHNICALS
• Price: {format_price(current_price)} ({change_24h:+.2f}%)
• RSI(14): {rsi:.1f}
• EMA(20): {format_price(ema20)}
• EMA(50): {format_price(ema50)}
• Volume Ratio: {volume_ratio:.2f}x

🎯 STRATEGY
• Entry: {format_price(entry)}
• Target: {format_price(target)}
• Stop: {format_price(stop)}
• Risk/Reward: 1:{risk_reward:.2f}

📌 KEY LEVELS
• Support: {format_price(low_24h)}
• Resistance: {format_price(high_24h)}

⚠️ Risk Disclosure: This is NOT financial advice. Always manage risk."""
        
        return AgentResponse(message={"role": "assistant", "content": result})

    except Exception as e:
        raise HTTPException(status_code=500, detail="Analysis error")


@app.get("/health")
async def health_check():
    return {"status": "ok", "x402": True}


@app.get("/")
async def root():
    return {"service": "Crypto Snapshot Pro x402 Agent", "agentId": "3613", "x402": True}
