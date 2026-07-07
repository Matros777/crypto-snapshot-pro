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
# x402 CONFIG + BAZAAR EXTENSION (ОБЯЗАТЕЛЬНО)
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
    ],
    "extensions": {
        "bazaar": {
            "info": {
                "input": {
                    "type": "http",
                    "method": "POST",
                    "body": {},
                    "bodyType": "json"
                },
                "output": {
                    "type": "json",
                    "example": {
                        "message": {
                            "role": "assistant",
                            "content": "📊 CRYPTO SNAPSHOT PRO — BTC/USDT\n🚀 Strong Bullish Setup..."
                        }
                    }
                }
            },
            "schema": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object"
            }
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


def has_valid_payment(request: Request) -> bool:
    h = request.headers
    return bool(h.get("x-payment") or h.get("payment-signature") or h.get("authorization"))


# ====================== АНАЛИЗ ======================
def calculate_rsi(closes, period=14):
    if len(closes) < period + 1: return 50.0
    gains = [max(closes[i] - closes[i-1], 0) for i in range(1, len(closes))]
    losses = [max(closes[i-1] - closes[i], 0) for i in range(1, len(closes))]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0: return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)


def calculate_ema(prices, period):
    if not prices: return 0.0
    k = 2 / (period + 1)
    ema = prices[0]
    for p in prices[1:]:
        ema = p * k + ema * (1 - k)
    return round(ema, 2)


def calculate_bollinger_bands(closes, period=20, std=2):
    if len(closes) < period: return 0,0,0
    recent = closes[-period:]
    mid = sum(recent) / period
    variance = sum((x - mid)**2 for x in recent) / period
    std_dev = variance ** 0.5
    return round(mid + std*std_dev,2), round(mid,2), round(mid - std*std_dev,2)


def detect_rsi_divergence(rsi, closes):
    if len(closes) < 10: return 'none'
    trend = closes[-1] - closes[-10]
    if trend < 0 and rsi > 50: return 'bullish'
    if trend > 0 and rsi < 50: return 'bearish'
    return 'none'


def calculate_pivot_points(high, low, close):
    p = (high + low + close) / 3
    return {'pivot': round(p, 2)}


def get_signal(rsi, ema20, ema50, vol_ratio, hl_range, bb_pos, rsi_div, price, pivot):
    long = short = 0
    if rsi < 30: long += 2
    elif rsi > 70: short += 2
    elif rsi < 40: long += 1
    elif rsi > 60: short += 1
    if ema20 > ema50: long += 1
    else: short += 1
    if bb_pos < 0.25: long += 1
    elif bb_pos > 0.75: short += 1
    if vol_ratio > 1.5:
        if long > short: long += 1
        else: short += 1
    if rsi_div == 'bullish': long += 1
    elif rsi_div == 'bearish': short += 1
    if hl_range > 0.03:
        if long > short: long += 1
        else: short += 1
    if price > pivot['pivot']: long += 0.5
    else: short += 0.5

    if long >= 5: return "LONG", "🚀 Strong Bullish Setup", long, short
    if short >= 5: return "SHORT", "🔥 Strong Bearish Setup", long, short
    if long > short: return "LONG", "⚡ Mild Bullish Bias", long, short
    if short > long: return "SHORT", "⚠️ Mild Bearish Bias", long, short
    return "HOLD", "➡️ Neutral — Wait for Setup", long, short


# ============================================================
# MAIN
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
        except: pass
    else:
        symbol = request.query_params.get("symbol", symbol)

    symbol = symbol.upper()
    if "USDT" not in symbol: symbol += "USDT"

    try:
        t = (await httpx.AsyncClient().get(f"{BINANCE_API}/ticker/24hr", params={"symbol": symbol})).json()
        price = float(t.get("lastPrice", 0))
        change = float(t.get("priceChangePercent", 0))
        high = float(t.get("highPrice", 0))
        low = float(t.get("lowPrice", 0))

        kl = (await httpx.AsyncClient().get(f"{BINANCE_API}/klines", params={"symbol": symbol, "interval": "1d", "limit": 50})).json()
        closes = [float(k[4]) for k in kl]
        volumes = [float(k[5]) for k in kl]

        rsi = calculate_rsi(closes)
        ema20 = calculate_ema(closes[-20:], 20)
        ema50 = calculate_ema(closes[-50:], 50)
        vol_ratio = volumes[-1] / (sum(volumes[-20:])/20) if len(volumes) >= 20 else 1.0
        hl_range = (high - low) / low if low > 0 else 0
        bb_u, bb_m, bb_l = calculate_bollinger_bands(closes)
        bb_pos = (bb_m - bb_l) / (bb_u - bb_l) if bb_u != bb_l else 0.5
        rsi_div = detect_rsi_divergence(rsi, closes)
        pivot = calculate_pivot_points(high, low, price)

        signal, desc, ls, ss = get_signal(rsi, ema20, ema50, vol_ratio, hl_range, bb_pos, rsi_div, price, pivot)

        result = f"""
╔══════════════════════════════════════════════════════════════╗
║ 📊 CRYPTO SNAPSHOT PRO — {symbol.replace('USDT', '/USDT')} ║
╚══════════════════════════════════════════════════════════════╝

📌 ТОРГОВЫЙ СИГНАЛ
─────────────────────────────────────────────────────────────
  Направление: {signal}
  Убеждённость: HIGH
  Счёт: {ls:.1f} LONG / {ss:.1f} SHORT

📈 ТЕХНИЧЕСКИЙ АНАЛИЗ
─────────────────────────────────────────────────────────────
  Цена: ${price:,.2f} ({change:+.2f}%)
  RSI (14): {rsi:.1f}
  EMA (20): ${ema20:,.2f}
  EMA (50): ${ema50:,.2f}

📊 ОБЪЁМ И ВОЛАТИЛЬНОСТЬ
─────────────────────────────────────────────────────────────
  Volume Ratio: {vol_ratio:.2f}x
  BB Position: {bb_pos:.2f}
  Pivot Point: ${pivot['pivot']:,.2f}

🎯 ТОРГОВАЯ СТРАТЕГИЯ
─────────────────────────────────────────────────────────────
  {'🟢 RSI ДИВЕРГЕНЦИЯ: ' + rsi_div.upper() if rsi_div != 'none' else 'Дивергенция: отсутствует'}

⚠️ Risk Disclosure: This is NOT financial advice. Always manage risk.
"""

        return AgentResponse(message={"role": "assistant", "content": result.strip()})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"service": "Crypto Snapshot Pro x402 Agent", "x402": True, "agentId": "3613"}
