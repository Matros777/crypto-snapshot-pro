# mcp_server.py
from fastmcp import FastMCP
import httpx
import json
import asyncio
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

# Создаем MCP сервер
mcp = FastMCP("Crypto Snapshot Pro")

@mcp.tool()
async def crypto_snapshot(symbol: str) -> dict:
    """
    Get AI-powered crypto market analysis for any cryptocurrency.
    
    Returns:
    - LONG, SHORT, or HOLD signal
    - Entry, Target, and Stop levels
    - Risk/Reward ratio
    - Professional AI analysis
    
    Supports 500+ pairs: BTC, ETH, SOL, DOGE, XRP, and more.
    Price: 0.025 USDC via x402 protocol on Base network.
    """
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://crypto-snapshot-pro.onrender.com/",
                json={"symbol": symbol}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "content" in data["message"]:
                    return {
                        "status": "success",
                        "analysis": data["message"]["content"],
                        "symbol": symbol
                    }
                return {
                    "status": "success",
                    "data": data,
                    "symbol": symbol
                }
            elif response.status_code == 402:
                return {
                    "status": "payment_required",
                    "message": "Payment required for this request",
                    "pay_to": "0x5b7efd37546d6BB02463339cEaDdD80997aC97B3",
                    "amount": "0.025 USDC",
                    "network": "Base"
                }
            else:
                return {
                    "status": "error",
                    "message": f"API error: {response.status_code}",
                    "symbol": symbol
                }
                
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "symbol": symbol
        }

@mcp.tool()
async def get_supported_pairs() -> list:
    """
    Get list of supported cryptocurrency pairs.
    Returns all Binance USDT pairs.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://api.binance.com/api/v3/exchangeInfo"
            )
            
            if response.status_code == 200:
                data = response.json()
                symbols = [
                    s["symbol"] for s in data["symbols"] 
                    if s["quoteAsset"] == "USDT" and s["status"] == "TRADING"
                ]
                return symbols[:50]
            return []
    except:
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"]

@mcp.resource("crypto://analysis/{symbol}")
async def get_analysis_resource(symbol: str) -> str:
    """
    Get analysis as a resource.
    """
    result = await crypto_snapshot(symbol)
    if result.get("status") == "success":
        return result.get("analysis", "Analysis not available")
    return f"Error: {result.get('message', 'Unknown error')}"

@mcp.prompt()
async def trading_prompt(symbol: str) -> str:
    """
    Generate a trading prompt for a specific symbol.
    """
    return f"""
    You are a professional crypto trader analyzing {symbol}.
    
    Please provide:
    1. Technical analysis
    2. Entry/exit points
    3. Risk management
    4. Market sentiment
    """

# ============================================================
# ДОПОЛНИТЕЛЬНЫЙ ЭНДПОИНТ ДЛЯ AGENTIC MARKET
# ============================================================

# Получаем http_app для монтирования
http_app = mcp.http_app()

# Добавляем информационный эндпоинт
@http_app.get("/info")
async def mcp_info():
    return {
        "name": "Crypto Snapshot Pro",
        "version": "1.0.0",
        "type": "mcp",
        "protocol": "streamable-http",
        "tools": [
            {
                "name": "crypto_snapshot",
                "description": "Get AI crypto analysis for any symbol",
                "parameters": {
                    "symbol": {"type": "string", "description": "Cryptocurrency symbol (BTC, ETH, SOL, etc.)"}
                }
            },
            {
                "name": "get_supported_pairs",
                "description": "Get list of supported crypto pairs",
                "parameters": {}
            }
        ],
        "resources": [
            {
                "uri": "crypto://analysis/{symbol}",
                "description": "Get analysis as a resource"
            }
        ],
        "price": "0.025 USDC",
        "network": "Base",
        "pay_to": "0x5b7efd37546d6BB02463339cEaDdD80997aC97B3"
    }

@http_app.get("/health")
async def health():
    return {"status": "ok", "service": "MCP Server"}

# Экспортируем для импорта в server.py
# mcp и http_app уже доступны

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
