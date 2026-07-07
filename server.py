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
from typing import Optional
import logging
import sys

# ============================================================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ============================================================
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("crypto-snapshot")

app = FastAPI(title="Crypto Snapshot Pro x402 Agent")

BINANCE_API = "https://api.binance.com/api/v3"
_cache = {}
_CACHE_TTL = 30


class AgentResponse(BaseModel):
    message: dict


# ============================================================
# x402 PAYMENT CONFIGURATION
# ============================================================
PAYMENT_CONFIG = {
    "x402Version": 2,
    "resource": {
        "url": "https://crypto-snapshot-pro.onrender.com",
        "description": "Real-time crypto market analysis using 8-factor scoring: RSI, EMA(20/50), Volume Ratio, Bollinger Bands, RSI Divergence, ATR volatility, Pivot Points. Price: $0.025 per request.",
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
            "extra": {
                "name": "USD Coin",
                "version": "2"
            }
        }
    ],
    "extensions": {
        "bazaar": {
            "info": {
                "input": {"type": "http", "method": "POST", "body": {}, "bodyType": "json"},
                "output": {"type": "json", "example": {"message": {"role": "assistant", "content": "..."}}}
            },
            "schema": {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object"}
        }
    }
}


def create_402_response():
    envelope = json.dumps(PAYMENT_CONFIG)
    encoded = base64.b64encode(envelope.encode("utf-8")).decode("utf-8")
    logger.info("🔐 402 Payment Required response generated")
    return Response(
        content="Payment Required",
        status_code=402,
        headers={"payment-required": encoded}
    )


# ============================================================
# 8-ФАКТОРНЫЙ АНАЛИЗ
# ============================================================

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
        return 0
    multiplier = 2 / (period + 1)
    ema = prices[0]
    for price in prices[1:]:
        ema = (price - ema) * multiplier + ema
    return round(ema, 2)


def calculate_macd(closes: list[float]) -> tuple[float, float, float]:
    if len(closes) < 26:
        return 0.0, 0.0, 0.0
    ema12 = calculate_ema(closes, 12)
    ema26 = calculate_ema(closes, 26)
    macd = ema12 - ema26
    macd_values = [macd]
    signal = calculate_ema(macd_values, 9) if len(macd_values) >= 9 else macd
    histogram = macd - signal
    return round(macd, 2), round(signal, 2), round(histogram, 2)


def calculate_bollinger_bands(closes: list[float], period: int = 20, std_dev: float = 2) -> tuple[float, float, float]:
    if len(closes) < period:
        return 0.0, 0.0, 0.0
    recent = closes[-period:]
    middle = sum(recent) / period
    variance = sum((x - middle) ** 2 for x in recent) / period
    std = variance ** 0.5
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    return round(upper, 2), round(middle, 2), round(lower, 2)


def detect_rsi_divergence(rsi: float, closes: list[float]) -> str:
    if len(closes) < 10:
        return 'none'
    recent_closes = closes[-10:]
    price_trend = recent_closes[-1] - recent_closes[0]
    if price_trend < 0 and rsi > 50:
        return 'bullish'
    elif price_trend > 0 and rsi < 50:
        return 'bearish'
    return 'none'


def calculate_pivot_points(high: float, low: float, close: float) -> dict:
    pivot = (high + low + close) / 3
    r1 = 2 * pivot - low
    s1 = 2 * pivot - high
    r2 = pivot + (high - low)
    s2 = pivot - (high - low)
    return {
        'pivot': round(pivot, 2),
        'r1': round(r1, 2),
        's1': round(s1, 2),
        'r2': round(r2, 2),
        's2': round(s2, 2)
    }


def get_signal_from_factors(rsi: float, price_ema20: float, price_ema50: float,
                           volume_ratio: float, high_low_range: float,
                           macd: float, macd_signal: float, macd_hist: float,
                           bb_upper: float, bb_middle: float, bb_lower: float,
                           rsi_divergence: str, pivot: dict) -> tuple[str, str, int, int]:
    long_score, short_score = 0, 0
    if rsi < 30:
        long_score += 2
    elif rsi > 70:
        short_score += 2
    elif rsi < 40:
        long_score += 1
    elif rsi > 60:
        short_score += 1
    if price_ema20 > price_ema50:
        long_score += 1
    else:
        short_score += 1
    if macd > macd_signal and macd_hist > 0:
        long_score += 1
    elif macd < macd_signal and macd_hist < 0:
        short_score += 1
    if bb_upper > 0 and bb_lower > 0:
        bb_position = (bb_middle - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
        if bb_position < 0.2:
            long_score += 1
        elif bb_position > 0.8:
            short_score += 1
    if volume_ratio > 1.5:
        if long_score > short_score:
            long_score += 1
        else:
            short_score += 1
    if rsi_divergence == 'bullish':
        long_score += 1
    elif rsi_divergence == 'bearish':
        short_score += 1
    if high_low_range > 0.03:
        if long_score > short_score:
            long_score += 1
        else:
            short_score += 1
    if pivot:
        current_price = bb_middle
        if current_price > pivot['pivot']:
            long_score += 0.5
        else:
            short_score += 0.5
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
    elif price >= 0.01:
        return f"${price:.4f}"
    return f"${price:.6f}"


async def fetch_ticker(symbol: str) -> dict:
    cache_key = f"ticker_{symbol}"
    now = time.time()
    if cache_key in _cache and now - _cache[cache_key]["time"] < _CACHE_TTL:
        logger.debug(f"📦 Cache hit for ticker {symbol}")
        return _cache[cache_key]["data"]
    async with httpx.AsyncClient(timeout=10.0) as client:
        logger.info(f"🌐 Fetching ticker for {symbol} from Binance")
        response = await client.get(f"{BINANCE_API}/ticker/24hr", params={"symbol": symbol})
        if response.status_code != 200:
            logger.error(f"❌ Binance API error for {symbol}: {response.text}")
            raise HTTPException(status_code=400, detail=f"Binance API error: {response.text}")
        data = response.json()
        if not data or "lastPrice" not in data:
            logger.error(f"❌ Symbol {symbol} not found on Binance")
            raise HTTPException(status_code=400, detail=f"Symbol {symbol} not found on Binance")
        _cache[cache_key] = {"data": data, "time": now}
        logger.debug(f"✅ Ticker data fetched for {symbol}")
        return data


async def fetch_klines(symbol: str, interval: str = "1d", limit: int = 50) -> list[dict]:
    cache_key = f"kline_{symbol}_{interval}_{limit}"
    now = time.time()
    if cache_key in _cache and now - _cache[cache_key]["time"] < _CACHE_TTL:
        logger.debug(f"📦 Cache hit for klines {symbol}")
        return _cache[cache_key]["data"]
    async with httpx.AsyncClient(timeout=10.0) as client:
        logger.info(f"🌐 Fetching klines for {symbol} from Binance")
        response = await client.get(f"{BINANCE_API}/klines", params={
            "symbol": symbol, "interval": interval, "limit": limit
        })
        if response.status_code != 200:
            logger.error(f"❌ Binance API error for klines {symbol}: {response.text}")
            raise HTTPException(status_code=400, detail=f"Binance API error: {response.text}")
        data = response.json()
        klines = []
        for k in data:
            klines.append({
                "close": float(k[4]),
                "high": float(k[2]),
                "low": float(k[3]),
                "volume": float(k[5]),
                "time": k[0]
            })
        _cache[cache_key] = {"data": klines, "time": now}
        logger.debug(f"✅ Klines data fetched for {symbol}")
        return klines


# ============================================================
# ОСНОВНОЙ ЭНДПОИНТ С ДЕТАЛЬНЫМ ЛОГИРОВАНИЕМ
# ============================================================
@app.api_route("/", methods=["GET", "POST"])
async def crypto_snapshot(request: Request):
    logger.info("=" * 80)
    logger.info("📨 NEW REQUEST RECEIVED")
    logger.info(f"📍 Method: {request.method}")
    logger.info(f"📍 URL: {request.url}")
    
    # Логируем все заголовки
    logger.info("📋 REQUEST HEADERS:")
    for key, value in request.headers.items():
        logger.info(f"  {key}: {value}")
    
    # Логируем тело запроса для POST
    body = None
    if request.method == "POST":
        try:
            body = await request.json()
            logger.info(f"📦 REQUEST BODY: {json.dumps(body, indent=2)}")
        except:
            logger.warning("⚠️ Could not parse request body as JSON")
    
    # Проверка платежа
    h = request.headers
    has_payment = bool(
        h.get("authorization") or 
        h.get("x-payment") or 
        h.get("payment-signature") or
        h.get("x-payment-signature") or
        h.get("authorization", "").startswith("Bearer")
    )
    logger.info(f"🔑 Payment check result: {has_payment}")
    logger.info(f"  - authorization: {h.get('authorization', 'MISSING')}")
    logger.info(f"  - x-payment: {h.get('x-payment', 'MISSING')}")
    logger.info(f"  - payment-signature: {h.get('payment-signature', 'MISSING')}")
    logger.info(f"  - x-payment-signature: {h.get('x-payment-signature', 'MISSING')}")
    
    if not has_payment:
        logger.warning("🚫 No payment detected — returning 402")
        return create_402_response()
    
    logger.info("✅ Payment detected — processing request")
    
    # Определяем символ
    symbol = "ETH"
    if request.method == "POST" and body:
        symbol = body.get("symbol", symbol)
    else:
        symbol = request.query_params.get("symbol", symbol)
    
    logger.info(f"📊 Symbol requested: {symbol}")
    
    symbol = symbol.upper()
    if "USDT" not in symbol:
        symbol += "USDT"
    
    logger.info(f"🔄 Normalized symbol: {symbol}")

    try:
        logger.info("⏳ Fetching market data...")
        ticker = await fetch_ticker(symbol)
        current_price = float(ticker.get("lastPrice", 0))
        change_24h = float(ticker.get("priceChangePercent", 0))
        high_24h = float(ticker.get("highPrice", 0))
        low_24h = float(ticker.get("lowPrice", 0))
        logger.info(f"📈 Price: {current_price}, Change: {change_24h}%")

        if current_price == 0:
            logger.error(f"❌ Invalid price for {symbol}")
            raise HTTPException(status_code=400, detail=f"Invalid price for {symbol}")

        klines = await fetch_klines(symbol)
        closes = [k["close"] for k in klines]
        volumes = [k["volume"] for k in klines]
        logger.info(f"📊 Data points: {len(closes)} closes, {len(volumes)} volumes")

        # Расчет индикаторов
        logger.info("🧮 Calculating indicators...")
        rsi = calculate_rsi(closes, 14)
        ema20 = calculate_ema(closes[-20:], 20) if len(closes) >= 20 else closes[-1]
        ema50 = calculate_ema(closes[-50:], 50) if len(closes) >= 50 else closes[-1]
        avg_volume = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else volumes[-1]
        current_volume = volumes[-1] if volumes else 0
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        high_low_range = (high_24h - low_24h) / low_24h if low_24h > 0 else 0

        macd, macd_signal, macd_hist = calculate_macd(closes)
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(closes)
        rsi_divergence = detect_rsi_divergence(rsi, closes)
        pivot = calculate_pivot_points(high_24h, low_24h, current_price)

        logger.info(f"📊 RSI: {rsi:.1f}, EMA20: {ema20:.2f}, EMA50: {ema50:.2f}")
        logger.info(f"📊 Volume Ratio: {volume_ratio:.2f}, BB Position: {(bb_middle - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5:.2f}")

        signal, signal_desc, long_score, short_score = get_signal_from_factors(
            rsi, ema20, ema50, volume_ratio, high_low_range,
            macd, macd_signal, macd_hist,
            bb_upper, bb_middle, bb_lower,
            rsi_divergence, pivot
        )

        logger.info(f"🎯 Signal: {signal} (LONG: {long_score}, SHORT: {short_score})")

        atr_proxy = high_low_range * current_price
        support = low_24h
        resistance = high_24h

        if signal == "LONG":
            entry = support + (resistance - support) * 0.2
            target = entry + (entry - support) * 2
            stop = support - atr_proxy * 0.5
            risk_reward = (target - entry) / (entry - stop) if entry > stop else 0
        elif signal == "SHORT":
            entry = resistance - (resistance - support) * 0.2
            target = entry - (resistance - entry) * 2
            stop = resistance + atr_proxy * 0.5
            risk_reward = (entry - target) / (stop - entry) if stop > entry else 0
        else:
            entry = current_price
            target = current_price * 1.05
            stop = current_price * 0.95
            risk_reward = 1.0

        total_score = long_score + short_score
        if total_score >= 5:
            conviction = "VERY HIGH"
        elif total_score >= 4:
            conviction = "HIGH"
        elif total_score >= 3:
            conviction = "MEDIUM"
        else:
            conviction = "LOW"

        result = f"""📊 CRYPTO SNAPSHOT PRO — {symbol.replace('USDT', '/USDT')}

{signal_desc}
📊 Conviction: {conviction}
🎯 Score: {long_score} LONG / {short_score} SHORT
💡 Reason: {'Bullish factors dominate.' if long_score > short_score else 'Bearish factors dominate.' if short_score > long_score else 'Mixed signals. Wait for confirmation.'}

📈 TECHNICALS
• Price: {format_price(current_price)} ({change_24h:+.2f}%)
• RSI(14): {rsi:.1f} ({'oversold' if rsi < 30 else 'overbought' if rsi > 70 else 'neutral'})
• EMA(20): {format_price(ema20)}
• EMA(50): {format_price(ema50)}
• Volume Ratio: {volume_ratio:.2f}x

🎯 STRATEGY
• Entry: {format_price(entry)}
• Target: {format_price(target)}
• Stop: {format_price(stop)}
• Risk/Reward: 1:{risk_reward:.2f}

📌 KEY LEVELS
• Support: {format_price(support)}
• Resistance: {format_price(resistance)}
• 24h High: {format_price(high_24h)}
• 24h Low: {format_price(low_24h)}
"""
        result += "\n\n⚠️ Risk Disclosure: This is NOT financial advice. Always manage risk. Past performance does not guarantee future results."
        
        logger.info("✅ Response generated successfully")
        logger.info("=" * 80)
        return AgentResponse(message={"role": "assistant", "content": result})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Internal error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/health")
async def health_check():
    logger.info("❤️ Health check")
    return {"status": "ok", "service": "crypto-snapshot-pro"}


@app.get("/")
async def root():
    logger.info("🏠 Root endpoint called")
    return {
        "service": "Crypto Snapshot Pro x402 Agent",
        "agentId": "3613",
        "version": "3.2.0",
        "data_source": "Binance Public API",
        "supported_pairs": "All Binance spot pairs (BTCUSDT, ETHUSDT, SOLUSDT, etc.)",
        "features": ["RSI", "EMA Trend", "Volume Anomaly", "Volatility", "8-Factor Scoring"],
        "x402": True,
        "settle": "CDP Facilitator",
        "endpoints": {
            "/": "Main endpoint (POST/GET)",
            "/payable": "x402 verification endpoint (POST)",
            "/health": "Health check (GET)",
        }
    }
