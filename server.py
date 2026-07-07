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
# ЛОГИРОВАНИЕ
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("crypto-snapshot")

app = FastAPI(title="Crypto Snapshot Pro x402 Agent")

BINANCE_API = "https://api.binance.com/api/v3"
_cache = {}
_CACHE_TTL = 30

# ============================================================
# КОНФИГУРАЦИЯ X402 V2
# ============================================================
FACILITATOR_URL = "https://api.cdp.coinbase.com/platform/v2/x402"

PAYMENT_CONFIG = {
    "x402Version": 2,
    "resource": {
        "url": "https://crypto-snapshot-pro.onrender.com/api/snapshot",
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

# ============================================================
# X402 PAYMENT FUNCTIONS
# ============================================================
def create_402_response():
    """Создает корректный 402 Payment Required ответ."""
    envelope = json.dumps(PAYMENT_CONFIG)
    encoded = base64.b64encode(envelope.encode("utf-8")).decode("utf-8")
    logger.info("🔐 402 Payment Required response generated")
    return Response(
        content="Payment Required",
        status_code=402,
        headers={"payment-required": encoded}
    )

async def verify_payment_with_facilitator(payment_payload: str) -> bool:
    """
    Отправляет payment payload в CDP Facilitator для верификации.
    """
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # 1. Отправляем на верификацию
            verify_response = await client.post(
                f"{FACILITATOR_URL}/verify",
                json={
                    "x402Version": 2,
                    "paymentPayload": payment_payload,
                    "paymentRequirements": PAYMENT_CONFIG["accepts"][0]
                },
                headers={"Content-Type": "application/json"}
            )
            
            if verify_response.status_code != 200:
                logger.error(f"❌ Facilitator verify failed: {verify_response.status_code}")
                return False

            # 2. Если верификация успешна — делаем settle
            settle_response = await client.post(
                f"{FACILITATOR_URL}/settle",
                json={
                    "x402Version": 2,
                    "paymentPayload": payment_payload,
                    "paymentRequirements": PAYMENT_CONFIG["accepts"][0]
                },
                headers={"Content-Type": "application/json"}
            )
            
            if settle_response.status_code != 200:
                logger.error(f"❌ Facilitator settle failed: {settle_response.status_code}")
                return False

            logger.info("✅ Payment verified and settled by facilitator")
            return True

    except Exception as e:
        logger.error(f"❌ Facilitator error: {e}")
        return False

# ============================================================
# 8-ФАКТОРНЫЙ АНАЛИЗ (ВСЕ ФУНКЦИИ ОСТАЮТСЯ)
# ============================================================
# ... (здесь все твои функции анализа, они не меняются) ...

# ============================================================
# ОСНОВНОЙ ЭНДПОИНТ АГЕНТА
# ============================================================
@app.post("/api/snapshot")
async def snapshot_endpoint(request: Request):
    """
    Основной эндпоинт для получения анализа. Требует валидный x402 v2 платёж.
    """
    logger.info("=" * 80)
    logger.info("📨 NEW SNAPSHOT REQUEST RECEIVED")
    
    # 1. Проверяем наличие платежного заголовка
    payment_header = request.headers.get("x-payment") or request.headers.get("payment-signature")
    
    if not payment_header:
        logger.warning("🚫 No payment header — returning 402")
        return create_402_response()
    
    logger.info("✅ Payment header detected, length: %s", len(payment_header))
    
    # 2. Валидируем платеж через фасилитатор
    if not await verify_payment_with_facilitator(payment_header):
        logger.error("❌ Payment verification failed")
        return create_402_response()
    
    # 3. Платёж валиден — выполняем анализ
    try:
        body = await request.json()
        symbol = body.get("symbol", "ETH")
        logger.info(f"📊 Analyzing symbol: {symbol}")
        
        # ... (здесь твой код анализа и формирования ответа) ...
        
        # Временный ответ (замени на свой анализ)
        result = f"📊 CRYPTO SNAPSHOT PRO — {symbol}/USDT\n✅ Payment verified and settled by facilitator.\n✅ Analysis complete."
        
        return {"message": {"role": "assistant", "content": result}}
        
    except Exception as e:
        logger.error(f"❌ Analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/info")
async def service_info():
    """Информация о сервисе."""
    return {
        "service": "Crypto Snapshot Pro x402 Agent",
        "agentId": "3613",
        "version": "3.2.0",
        "x402": True,
        "price": "0.025 USDC per request",
        "network": "Base"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "crypto-snapshot-pro"}

# ============================================================
# ЭНДПОИНТЫ ДЛЯ MARKETPLACE
# ============================================================
@app.post("/verify")
async def verify_endpoint(request: Request):
    """
    Эндпоинт для верификации платежа через фасилитатор.
    """
    try:
        body = await request.json()
        payment_payload = body.get("paymentPayload")
        payment_requirements = body.get("paymentRequirements")
        
        if not payment_payload or not payment_requirements:
            raise HTTPException(status_code=400, detail="Missing paymentPayload or paymentRequirements")
        
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{FACILITATOR_URL}/verify",
                json={
                    "x402Version": 2,
                    "paymentPayload": payment_payload,
                    "paymentRequirements": payment_requirements
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return {"status": "verified", "isValid": True}
            else:
                raise HTTPException(status_code=402, detail="Payment verification failed")
                
    except Exception as e:
        logger.error(f"❌ Verify endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
