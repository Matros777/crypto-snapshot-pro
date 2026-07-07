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

app = FastAPI(title="Crypto Snapshot Pro x402 Agent")

BINANCE_API = "https://api.binance.com/api/v3"
_cache = {}
_CACHE_TTL = 30


class AgentResponse(BaseModel):
    message: dict


# ============================================================
# x402 CONFIG WITH DOMAIN (FIXED)
# ============================================================
PAYMENT_CONFIG = {
    "x402Version": 2,
    "resource": {
        "url": "https://crypto-snapshot-pro.onrender.com",
        "description": "Real-time crypto market analysis using 8-factor scoring: RSI, EMA(20/50), Volume Ratio, Bollinger Bands, RSI Divergence, ATR Volatility, Pivot Points. Price: $0.025 per request.",
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
            "domain": {
                "name": "USD Coin",
                "version": "2",
                "chainId": 8453,
                "verifyingContract": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
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
    return Response(
        content="Payment Required",
        status_code=402,
        headers={"payment-required": encoded}
    )


async def verify_payment_with_facilitator(payment_payload: str) -> bool:
    """Verify payment through CDP Facilitator (Coinbase)"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.cdp.coinbase.com/platform/v2/x402/verify",
                json={"payment": payment_payload},
                headers={"Content-Type": "application/json"}
            )
            return resp.status_code == 200
    except Exception as e:
        print(f"Facilitator verification failed: {e}")
        return False


# ============================================================
# 8-FACTOR TECHNICAL ANALYSIS
# ============================================================

def calculate_rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50.0
    gains = [max(closes[i] - closes[i-1], 0) for i in range(1, len(closes))]
    losses = [max(closes[i-1] - closes[i], 0) for i in range(1, len(closes))]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)


def calculate_ema(prices, period):
    if not prices:
        return 0.0
    k = 2 / (period + 1)
    ema = prices[0]
    for p in prices[1:]:
        ema = p * k + ema * (1 - k)
    return round(ema, 2)


def calculate_bollinger_bands(closes, period=20, std=2):
    if len(closes) < period:
        return 0, 0, 0
    recent = closes[-period:]
    mid = sum(recent) / period
    variance = sum((x - mid) ** 2 for x in recent) / period
    std_dev = variance ** 0.5
    return round(mid + std * std_dev, 2), round(mid, 2), round(mid - std * std_dev, 2)


def detect_rsi_divergence(rsi, closes):
    if len(closes) < 10:
        return 'none'
    trend = closes[-1] - closes[-10]
    if trend < 0 and rsi > 50:
        return 'bullish'
    if trend > 0 and rsi < 50:
        return 'bearish'
    return 'none'


def calculate_pivot_points(high, low, close):
    p = (high + low + close) / 3
    return {'pivot': round(p, 2)}


def get_signal(rsi, ema20, ema50, vol_ratio, hl_range, bb_pos, rsi_div, price, pivot):
    long_score = 0
    short_score = 0

    # 1. RSI
    if rsi < 30:
        long_score += 2
    elif rsi > 70:
        short_score += 2
    elif rsi < 40:
        long_score += 1
    elif rsi > 60:
        short_score += 1

    # 2. EMA Trend
    if ema20 > ema50:
        long_score += 1
    else:
        short_score += 1

    # 3. Bollinger Bands Position
    if bb_pos < 0.25:
        long_score += 1
    elif bb_pos > 0.75:
        short_score += 1

    # 4. Volume Ratio
    if vol_ratio > 1.5:
        if long_score > short_score:
            long_score += 1
        else:
            short_score += 1

    # 5. RSI Divergence
    if rsi_div == 'bullish':
        long_score += 1
    elif rsi_div == 'bearish':
        short_score += 1

    # 6. Volatility (ATR Proxy)
    if hl_range > 0.03:
        if long_score > short_score:
            long_score += 1
        else:
            short_score += 1

    # 7. Pivot Points
    if price > pivot['pivot']:
        long_score += 0.5
    else:
        short_score += 0.5

    # Final Signal
    if long_score >= 5:
        return "LONG", "🚀 Strong Bullish Setup", long_score, short_score
    if short_score >= 5:
        return "SHORT", "🔥 Strong Bearish Setup", long_score, short_score
    if long_score > short_score:
        return "LONG", "⚡ Mild Bullish Bias", long_score, short_score
    if short_score > long_score:
        return "SHORT", "⚠️ Mild Bearish Bias", long_score, short_score
    return "HOLD", "➡️ Neutral — Wait for Setup", long_score, short_score


# ============================================================
# MAIN ENDPOINT
# ============================================================
@app.api_route("/", methods=["GET", "POST"])
async def crypto_snapshot(request: Request):
    # Payment verification
    payment_header = (
        request.headers.get("x-payment") or 
        request.headers.get("payment-signature") or 
        request.headers.get("authorization")
    )
    
    if not payment_header:
        return create_402_response()

    if not await verify_payment_with_facilitator(payment_header):
        raise HTTPException(status_code=402, detail="Payment verification failed by facilitator")

    # Get symbol
    symbol = "ETH"
    if request.method == "POST":
        try:
            body = await request.json()
            symbol = body.get("symbol", symbol)
        except:
            pass
    else:
        symbol = request.query_params.get("symbol", symbol)

    symbol = symbol.upper()
    if "USDT" not in symbol:
        symbol += "USDT"

    try:
        # Fetch market data
        async with httpx.AsyncClient() as client:
            ticker = await client.get(f"{BINANCE_API}/ticker/24hr", params={"symbol": symbol})
            ticker = ticker.json()
            
            klines = await client.get(
                f"{BINANCE_API}/klines",
                params={"symbol": symbol, "interval": "1d", "limit": 50}
            )
            klines = klines.json()

        price = float(ticker.get("lastPrice", 0))
        change = float(ticker.get("priceChangePercent", 0))
        high = float(ticker.get("highPrice", 0))
        low = float(ticker.get("lowPrice", 0))

        closes = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]

        # Calculate indicators
        rsi = calculate_rsi(closes)
        ema20 = calculate_ema(closes[-20:], 20)
        ema50 = calculate_ema(closes[-50:], 50)
        vol_ratio = volumes[-1] / (sum(volumes[-20:]) / 20) if len(volumes) >= 20 else 1.0
        hl_range = (high - low) / low if low > 0 else 0
        bb_u, bb_m, bb_l = calculate_bollinger_bands(closes)
        bb_pos = (bb_m - bb_l) / (bb_u - bb_l) if bb_u != bb_l else 0.5
        rsi_div = detect_rsi_divergence(rsi, closes)
        pivot = calculate_pivot_points(high, low, price)

        # Generate signal
        signal, desc, long_score, short_score = get_signal(
            rsi, ema20, ema50, vol_ratio, hl_range, bb_pos, rsi_div, price, pivot
        )

        # Conviction level
        total_score = long_score + short_score
        if total_score >= 6:
            conviction = "VERY HIGH"
        elif total_score >= 4:
            conviction = "HIGH"
        elif total_score >= 3:
            conviction = "MEDIUM"
        else:
            conviction = "LOW"

        # Build response
        result = f"""
╔══════════════════════════════════════════════════════════════╗
║ 📊 CRYPTO SNAPSHOT PRO — {symbol.replace('USDT', '/USDT')} ║
╚══════════════════════════════════════════════════════════════╝

📌 TRADING SIGNAL
─────────────────────────────────────────────────────────────
  Direction: {signal}
  Conviction: {conviction}
  Score: {long_score:.1f} LONG / {short_score:.1f} SHORT

📈 TECHNICAL ANALYSIS
─────────────────────────────────────────────────────────────
  Price: ${price:,.2f} ({change:+.2f}%)
  RSI (14): {rsi:.1f} ({'oversold' if rsi < 30 else 'overbought' if rsi > 70 else 'neutral'})
  EMA (20): ${ema20:,.2f}
  EMA (50): ${ema50:,.2f}
  EMA Trend: {'🟢 BULLISH' if ema20 > ema50 else '🔴 BEARISH'}

📊 VOLUME & VOLATILITY
─────────────────────────────────────────────────────────────
  Volume Ratio: {vol_ratio:.2f}x
  BB Position: {bb_pos:.2f} ({'overbought' if bb_pos > 0.7 else 'oversold' if bb_pos < 0.3 else 'neutral'})
  Pivot Point: ${pivot['pivot']:,.2f}

🎯 TRADING STRATEGY
─────────────────────────────────────────────────────────────
  {'🟢 RSI DIVERGENCE: ' + rsi_div.upper() if rsi_div != 'none' else 'No divergence detected'}

⚠️ DISCLAIMER: This is NOT financial advice. Trade at your own risk.
"""
        return AgentResponse(message={"role": "assistant", "content": result.strip()})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Crypto Snapshot Pro x402 Agent"}


@app.get("/")
async def root():
    return {
        "service": "Crypto Snapshot Pro x402 Agent",
        "agentId": "3613",
        "version": "3.2.0",
        "x402": True,
        "price": "0.025 USDC per request",
        "network": "Base",
        "features": [
            "RSI (14)",
            "EMA (20/50)",
            "Volume Ratio",
            "Bollinger Bands",
            "RSI Divergence",
            "ATR Volatility",
            "Pivot Points",
            "8-Factor Scoring System"
        ],
        "endpoints": {
            "/": "Main endpoint (POST/GET)",
            "/health": "Health check (GET)"
        }
    }
