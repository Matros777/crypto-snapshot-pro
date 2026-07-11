from fastmcp import FastMCP
import requests


mcp = FastMCP(
    name="Crypto Snapshot Pro"
)


@mcp.tool()
def crypto_snapshot(symbol: str):
    """
    Get AI crypto market signal.
    Supports 500+ crypto pairs.
    """

    response = requests.post(
        "https://crypto-snapshot-pro.onrender.com/",
        json={
            "symbol": symbol
        },
        timeout=120
    )

    return response.json()


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000
    )
