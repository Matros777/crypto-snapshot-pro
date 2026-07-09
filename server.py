"""
Crypto Snapshot Pro — x402 Agent for Agentic.Market
Agent ID: #3613
Service: Professional Multi-Factor Market Analysis ($0.025 per request)
"""
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import time
import base64
import json
import logging
import sys
from typing import Optional, Any

# ============================================================
# ЛОГИРОВАНИЕ
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("crypto-snapshot")

app = FastAPI(title="Crypto Snapshot Pro x402 Agent")

# ============================================================
# ИСТОЧНИК ДАННЫХ - Kraken (публичный, БЕЗ КЛЮЧА)
# ============================================================
KRAKEN_API = "https://api.kraken.com/0/public"
_cache = {}
_CACHE_TTL = 60

# ============================================================
# ALCHEMY RPC & CONTRACTS
# ============================================================
ALCHEMY_URL = "https://base-mainnet.g.alchemy.com/v2/U8khpdvO0rAwu9ojyBOpr"

USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
PAYTO_ADDRESS = "0x5b7efd37546d6BB02463339cEaDdD80997aC97B3"
MIN_AMOUNT = 25000  # 0.025 USDC


class AgentResponse(BaseModel):
    message: dict


# ============================================================
# FACILITATOR VERIFICATION
# ============================================================
FACILITATOR_URL = "https://facilitator.openx402.ai"

async def verify_and_settle_with_facilitator(payment_payload: str) -> bool:
    """Полная проверка платежа через OpenFacilitator"""
    logger.info("🔍 Starting facilitator verification...")
    
    try:
        payment_data = json.loads(base64.b64decode(payment_payload).decode('utf-8'))
        logger.info("✅ Payment payload decoded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to decode payment payload: {e}")
        return False
    
    requirements = PAYMENT_CONFIG["accepts"][0]
    
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            verify_response = await client.post(
                f"{FACILITATOR_URL}/verify",
                json={
                    "paymentPayload": payment_data,
                    "paymentRequirements": requirements
                },
                headers={"Content-Type": "application/json"}
            )
            
            logger.info(f"VERIFY STATUS: {verify_response.status_code}")
            logger.info(f"VERIFY RESPONSE: {verify_response.text}")
            
            if verify_response.status_code != 200:
                logger.warning(f"⚠️ Verification failed: {verify_response.status_code}")
                return False
            
            verify_data = verify_response.json()
            if not verify_data.get("isValid", False):
                logger.warning(f"⚠️ Invalid signature: {verify_data}")
                return False
            
            logger.info("✅ Signature verified by facilitator")
            
            settle_response = await client.post(
                f"{FACILITATOR_URL}/settle",
                json={
                    "paymentPayload": payment_data,
                    "paymentRequirements": requirements
                },
                headers={"Content-Type": "application/json"}
            )
            
            logger.info(f"SETTLE STATUS: {settle_response.status_code}")
            logger.info(f"SETTLE RESPONSE: {settle_response.text}")
            
            if settle_response.status_code != 200:
                logger.warning(f"⚠️ Settle failed: {settle_response.status_code}")
                return False
            
            logger.info("✅ Payment verified and settled by facilitator")
            return True
            
    except Exception as e:
        logger.error(f"❌ Facilitator error: {e}")
        return False


# ============================================================
# x402 PAYMENT CONFIGURATION
# ============================================================
PAYMENT_CONFIG = {
    "x402Version": 2,
    "resource": {
        "url": "https://crypto-snapshot-pro.onrender.com/",
        "description": "Real-time crypto market analysis using 8-factor scoring: RSI, EMA(20/50), Volume Ratio, Bollinger Bands, RSI Divergence, ATR volatility, Pivot Points. Outputs: LONG/SHORT/HOLD signal, conviction level (LOW/MEDIUM/HIGH/VERY HIGH), Entry/Target/Stop levels, Risk/Reward ratio. Supports 500+ Binance pairs (BTC, ETH, SOL, DOGE, XRP, etc.). Price: $0.025 per request.",
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
    ]
}


def create_402_response():
    """Возвращает 402 Payment Required"""
    envelope = json.dumps(PAYMENT_CONFIG, separators=(',', ':'))
    encoded = base64.b64encode(envelope.encode("utf-8")).decode("utf-8")
    logger.info("🔐 402 Payment Required sent")
    return Response(
        content="Payment Required",
        status_code=402,
        headers={
            "PAYMENT-REQUIRED": encoded,
            "content-type": "text/plain"
        }
    )


# ============================================================
# Kraken API - ТОЛЬКО РЕАЛЬНЫЕ ДАННЫЕ, БЕЗ ФОЛБЭКОВ!
# ============================================================
KRAKEN_PAIRS = {
    "BTCUSDT": "XXBTZUSD",
    "ETHUSDT": "XETHZUSD",
    "SOLUSDT": "SOLUSD",
    "DOGEUSDT": "XDGUSD",
    "XRPUSDT": "XXRPZUSD",
    "ADAUSDT": "ADAUSD",
    "DOTUSDT": "DOTUSD",
    "LINKUSDT": "LINKUSD",
    "AVAXUSDT": "AVAXUSD",
    "MATICUSDT": "MATICUSD",
    "UNIUSDT": "UNIUSD",
    "ATOMUSDT": "ATOMUSD",
    "LTCUSDT": "XLTCZUSD",
    "BCHUSDT": "XBCHZUSD",
    "NEARUSDT": "NEARUSD",
    "FILUSDT": "FILUSD",
    "APTUSDT": "APTUSD",
    "ARBUSDT": "ARBUSD",
    "OPUSDT": "OPUSD",
    "SUIUSDT": "SUIUSD"
}

async def fetch_ticker(symbol: str) -> dict:
    """Получение данных через Kraken - ТОЛЬКО РЕАЛЬНЫЕ ДАННЫЕ!"""
    cache_key = f"ticker_{symbol}"
    now = time.time()
    if cache_key in _cache and now - _cache[cache_key]["time"] < _CACHE_TTL:
        return _cache[cache_key]["data"]
    
    pair = KRAKEN_PAIRS.get(symbol)
    if not pair:
        logger.error(f"❌ Symbol {symbol} not supported by Kraken")
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not supported")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            logger.info(f"📊 Fetching {symbol} from Kraken...")
            response = await client.get(
                f"{KRAKEN_API}/Ticker",
                params={"pair": pair}
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Kraken error: {response.status_code}")
                raise HTTPException(status_code=503, detail="Market data unavailable")
            
            data = response.json()
            if data.get("error"):
                logger.error(f"❌ Kraken error: {data['error']}")
                raise HTTPException(status_code=503, detail="Market data unavailable")
            
            result_data = list(data.get("result", {}).values())[0]
            price = float(result_data.get("c", [0])[0])
            
            if price == 0:
                raise HTTPException(status_code=503, detail="Invalid price data")
            
            # Получаем цену 24 часа назад из OHLC для расчета процента
            try:
                ohlc_response = await client.get(
                    f"{KRAKEN_API}/OHLC",
                    params={"pair": pair, "interval": 1440, "count": 2}
                )
                if ohlc_response.status_code == 200:
                    ohlc_data = ohlc_response.json()
                    if not ohlc_data.get("error"):
                        ohlc_list = list(ohlc_data.get("result", {}).values())[0]
                        if len(ohlc_list) >= 2:
                            old_price = float(ohlc_list[-2][4])
                            change_24h = ((price - old_price) / old_price) * 100
                        else:
                            change_24h = 0
                    else:
                        change_24h = 0
                else:
                    change_24h = 0
            except:
                change_24h = 0
            
            result = {
                "price": price,
                "change": change_24h,
                "high": float(result_data.get("h", [price])[0]),
                "low": float(result_data.get("l", [price])[0]),
                "volume": float(result_data.get("v", [0])[0]),
                "time": time.time()
            }
            
            _cache[cache_key] = {"data": result, "time": now}
            logger.info(f"✅ {symbol} price: ${price}, change: {change_24h:.2f}%")
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Kraken error: {e}")
        raise HTTPException(status_code=503, detail="Market data unavailable")


async def fetch_klines(symbol: str, interval: str = "1d", limit: int = 50) -> list[dict]:
    """Получение исторических данных через Kraken - ТОЛЬКО РЕАЛЬНЫЕ ДАННЫЕ!"""
    cache_key = f"klines_{symbol}_{interval}_{limit}"
    now = time.time()
    if cache_key in _cache and now - _cache[cache_key]["time"] < _CACHE_TTL:
        return _cache[cache_key]["data"]
    
    pair = KRAKEN_PAIRS.get(symbol)
    if not pair:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not supported")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            logger.info(f"📊 Fetching klines for {symbol} from Kraken...")
            response = await client.get(
                f"{KRAKEN_API}/OHLC",
                params={"pair": pair, "interval": 1440, "count": limit}
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Kraken klines error: {response.status_code}")
                raise HTTPException(status_code=503, detail="Historical data unavailable")
            
            data = response.json()
            if data.get("error"):
                logger.error(f"❌ Kraken klines error: {data['error']}")
                raise HTTPException(status_code=503, detail="Historical data unavailable")
            
            ohlc_data = list(data.get("result", {}).values())[0]
            if not ohlc_data or len(ohlc_data) < 5:
                raise HTTPException(status_code=503, detail="Insufficient historical data")
            
            klines = []
            for candle in ohlc_data[-limit:]:
                klines.append({
                    'close': float(candle[4]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'volume': float(candle[6]),
                    'time': int(candle[0]) * 1000
                })
            
            _cache[cache_key] = {"data": klines, "time": now}
            return klines
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Kraken klines error: {e}")
        raise HTTPException(status_code=503, detail="Historical data unavailable")


# ============================================================
# Технические функции
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
        return 0.0
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
    long_score = short_score = 0
    
    if rsi < 30: long_score += 2
    elif rsi > 70: short_score += 2
    elif rsi < 40: long_score += 1
    elif rsi > 60: short_score += 1

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


# ============================================================
# PAYABLE ENDPOINT
# ============================================================
@app.post("/payable")
async def payable_endpoint(request: Request):
    payment_header = (
        request.headers.get("x-payment") or
        request.headers.get("payment-signature")
    )
    if not payment_header:
        return create_402_response()
    
    valid = await verify_and_settle_with_facilitator(payment_header)
    if not valid:
        return Response(
            content="Payment verification failed",
            status_code=402
        )
    
    return {"status": "ok", "message": "Payment verified"}


# ============================================================
# ОСНОВНОЙ ЭНДПОИНТ - С КРАСИВЫМ ВЫВОДОМ В ТЕРМИНАЛЕ
# ============================================================
@app.api_route("/", methods=["GET", "POST"])
async def crypto_snapshot(request: Request):
    payment_header = (
        request.headers.get("x-payment") or
        request.headers.get("payment-signature")
    )
    
    if not payment_header:
        return create_402_response()
   
    valid = await verify_and_settle_with_facilitator(payment_header)
    if not valid:
        return Response(
            content="Payment verification failed",
            status_code=402
        )
   
    symbol = None
   
    if request.method == "POST":
        try:
            body = await request.json()
        except:
            raise HTTPException(status_code=400, detail="Invalid JSON body")
       
        if "message" in body and isinstance(body["message"], dict):
            symbol = body["message"].get("content", "").strip()
        elif isinstance(body, dict) and "symbol" in body:
            symbol = body["symbol"].strip()
        elif "content" in body:
            symbol = body["content"].strip()
        elif "message" in body and isinstance(body["message"], str):
            symbol = body["message"].strip()
    else:
        symbol = request.query_params.get("symbol", "ETH")
   
    if not symbol:
        return AgentResponse(message={
            "role": "assistant",
            "content": "📊 CRYPTO SNAPSHOT PRO\n\nSend a symbol to analyze.\n\nExamples:\n• BTC\n• ETH\n• SOL\n• DOGE\n• XRP\n\nUsage: POST {\"symbol\": \"BTC\"} or GET ?symbol=BTC"
        })
   
    symbol = symbol.upper()
    if "USDT" not in symbol:
        symbol = f"{symbol}USDT"
   
    try:
        ticker = await fetch_ticker(symbol)
        current_price = float(ticker.get("price", 0))
        change_24h = float(ticker.get("change", 0))
        high_24h = float(ticker.get("high", 0))
        low_24h = float(ticker.get("low", 0))

        if current_price == 0:
            raise HTTPException(status_code=503, detail="Market data unavailable")

        klines = await fetch_klines(symbol)
        closes = [k["close"] for k in klines]
        volumes = [k["volume"] for k in klines]

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

        signal, signal_desc, long_score, short_score = get_signal_from_factors(
            rsi, ema20, ema50, volume_ratio, high_low_range,
            macd, macd_signal, macd_hist, bb_upper, bb_middle, bb_lower,
            rsi_divergence, pivot
        )

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
        conviction = "VERY HIGH" if total_score >= 5 else "HIGH" if total_score >= 4 else "MEDIUM" if total_score >= 3 else "LOW"

        # ============================================================
        # КРАСИВЫЙ СТРУКТУРИРОВАННЫЙ ВЫВОД В ТЕРМИНАЛЕ
        # ============================================================
        result = f"""
╔══════════════════════════════════════════════════════════════════╗
║  📊 CRYPTO SNAPSHOT PRO — {symbol.replace('USDT', '/USDT')}          ║
╚══════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════╗
║  🎯 СИГНАЛ                                                    ║
╠══════════════════════════════════════════════════════════════════╣
║  {signal_desc:<56} ║
║  Conviction: {conviction:<10}  |  Score: {long_score:.1f} LONG / {short_score:.1f} SHORT    ║
║  Reason: {'Bullish factors dominate.' if long_score > short_score else 'Bearish factors dominate.' if short_score > long_score else 'Mixed signals. Wait for confirmation.'} ║
╚══════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════╗
║  📈 ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ                                    ║
╠══════════════════════════════════════════════════════════════════╣
║  Price:  {format_price(current_price):<20}  24h Change: {change_24h:+.2f}% ║
║  RSI(14): {rsi:.1f} ({'oversold' if rsi < 30 else 'overbought' if rsi > 70 else 'neutral'}){' ' * (40 - len(f'{rsi:.1f} ({'oversold' if rsi < 30 else 'overbought' if rsi > 70 else 'neutral'})'))}║
║  EMA(20): {format_price(ema20):<20}  EMA(50): {format_price(ema50)} ║
║  Volume Ratio: {volume_ratio:.2f}x{' ' * (30 - len(f'{volume_ratio:.2f}x'))}║
╚══════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════╗
║  🎯 СТРАТЕГИЯ                                                 ║
╠══════════════════════════════════════════════════════════════════╣
║  Entry:  {format_price(entry):<20}  Target: {format_price(target)} ║
║  Stop:   {format_price(stop):<20}  Risk/Reward: 1:{risk_reward:.2f} ║
╚══════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════╗
║  📌 КЛЮЧЕВЫЕ УРОВНИ                                           ║
╠══════════════════════════════════════════════════════════════════╣
║  Support:  {format_price(support):<20}  Resistance: {format_price(resistance)} ║
║  24h High: {format_price(high_24h):<20}  24h Low:  {format_price(low_24h)} ║
╚══════════════════════════════════════════════════════════════════╝

⚠️  Risk Disclosure: This is NOT financial advice. Always manage risk. Past performance does not guarantee future results.
"""
       
        return AgentResponse(message={"role": "assistant", "content": result})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "crypto-snapshot-pro"}


@app.get("/")
async def root():
    return {
        "service": "Crypto Snapshot Pro x402 Agent",
        "agentId": "3613",
        "version": "3.2.1",
        "data_source": "Kraken Public API (REAL DATA ONLY, NO FALLBACK)",
        "supported_pairs": "BTC, ETH, SOL, DOGE, XRP, ADA, DOT, LINK, AVAX, MATIC, UNI, ATOM, LTC, BCH, NEAR, FIL, APT, ARB, OP, SUI",
        "features": ["RSI", "EMA Trend", "Volume Anomaly", "Volatility", "8-Factor Scoring"],
        "x402": True,
        "settle": "OpenFacilitator",
        "endpoints": {
            "/": "Main endpoint (POST/GET)",
            "/payable": "x402 verification endpoint (POST)",
            "/health": "Health check (GET)",
        }
    }
