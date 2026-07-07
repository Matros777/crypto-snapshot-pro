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
# x402 CONFIG
# ============================================================
PAYMENT_CONFIG = {
    "x402Version": 2,
    "resource": {
        "url": "https://crypto-snapshot-pro.onrender.com",
        "description": "Real-time crypto market analysis using 8-factor scoring. Price: $0.025 per request.",
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
    return Response(content="Payment Required", status_code=402, headers={"payment-required": encoded})


async def verify_payment_with_facilitator(payment_payload: str) -> bool:
    """Реальная проверка через facilitator (CDP / Coinbase)"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.cdp.coinbase.com/x402/verify",  # или актуальный endpoint facilitator
                json={"payment": payment_payload},
                headers={"Content-Type": "application/json"}
            )
            return resp.status_code == 200
    except:
        return False  # В продакшене лучше логировать


# ====================== АНАЛИЗ ======================
# (все 8 индикаторов — оставь как в предыдущей полной версии)


# ============================================================
# MAIN ENDPOINT
# ============================================================
@app.api_route("/", methods=["GET", "POST"])
async def crypto_snapshot(request: Request):
    # Строгая проверка
    payment_header = request.headers.get("x-payment") or request.headers.get("payment-signature") or request.headers.get("authorization")
    
    if not payment_header:
        return create_402_response()

    # Проверка через facilitator
    if not await verify_payment_with_facilitator(payment_header):
        raise HTTPException(status_code=402, detail="Payment verification failed by facilitator")

    # Если дошли сюда — платёж подтверждён, отдаём анализ
    # ... (весь твой код анализа с 8 индикаторами и красивым выводом)

    return AgentResponse(message={"role": "assistant", "content": result})


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"service": "Crypto Snapshot Pro x402 Agent", "x402": True, "agentId": "3613"}
