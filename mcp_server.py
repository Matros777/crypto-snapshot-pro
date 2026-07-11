# mcp_server.py - УПРОЩЕННАЯ ВЕРСИЯ (без fastmcp)
from fastapi import FastAPI, Request
import httpx
import json

# Создаем обычное FastAPI приложение для MCP
http_app = FastAPI(title="MCP Server")

@http_app.post("/")
async def mcp_handler(request: Request):
    """Обработчик MCP запросов."""
    try:
        body = await request.json()
        method = body.get("method", "")
        params = body.get("params", {})
        symbol = params.get("symbol", "BTC")
        
        # Вызываем основной API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://crypto-snapshot-pro.onrender.com/",
                json={"symbol": symbol}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "result": data
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {"code": response.status_code, "message": "Payment required"}
                }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": body.get("id", 1),
            "error": {"code": -32000, "message": str(e)}
        }

@http_app.get("/health")
async def health():
    return {"status": "ok", "service": "MCP Server"}

@http_app.get("/info")
async def info():
    return {
        "name": "Crypto Snapshot Pro",
        "version": "1.0.0",
        "type": "mcp",
        "endpoint": "/mcp"
    }

# Для совместимости с server.py
mcp = type('MCP', (), {'http_app': lambda: http_app})()
