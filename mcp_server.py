from fastmcp import FastMCP
import httpx

mcp = FastMCP("Crypto Snapshot Pro")

@mcp.tool
async def crypto_snapshot(symbol: str) -> dict:
    """
    AI crypto market analysis.
    Returns LONG, SHORT or HOLD signal.
    Supports 500+ crypto pairs.
    Price: 0.025 USDC via x402 protocol.
    """
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://crypto-snapshot-pro.onrender.com/",
            json={"symbol": symbol}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Payment required: {response.status_code}",
                "pay_to": "0x5b7efd37546d6BB02463339cEaDdD80997aC97B3",
                "amount": "0.025 USDC",
                "network": "Base"
            }
