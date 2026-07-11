# mcp_server.py - ПОЛНОСТЬЮ РАБОЧАЯ ВЕРСИЯ
from fastmcp import FastMCP
import httpx

# Создаем MCP сервер
mcp = FastMCP("Crypto Snapshot Pro")

@mcp.tool()
async def crypto_snapshot(symbol: str) -> dict:
    """Get AI crypto analysis for any symbol."""
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
                return {"status": "success", "data": data, "symbol": symbol}
            elif response.status_code == 402:
                return {
                    "status": "payment_required",
                    "message": "Payment required for this request",
                    "pay_to": "0x5b7efd37546d6BB02463339cEaDdD80997aC97B3",
                    "amount": "0.025 USDC",
                    "network": "Base"
                }
            return {"status": "error", "message": f"API error: {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def get_supported_pairs() -> list:
    """Get list of supported crypto pairs."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("https://api.binance.com/api/v3/exchangeInfo")
            if response.status_code == 200:
                data = response.json()
                return [s["symbol"] for s in data["symbols"] 
                       if s["quoteAsset"] == "USDT" and s["status"] == "TRADING"][:50]
            return []
    except:
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"]

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
