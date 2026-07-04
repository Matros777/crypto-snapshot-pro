# Crypto Snapshot Pro — A2A Endpoint for OKX.AI

**Agent ID:** #3613

Crypto Snapshot Pro is a real-time cryptocurrency technical analysis microservice built on FastAPI with A2A (Agent-to-Agent) protocol support. It provides instant, structured market snapshots for any supported crypto asset via a simple POST request.

---

## 🚀 Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/your-username/crypto-snapshot-pro.git
cd crypto-snapshot-pro

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Test the API

```bash
curl -X POST http://localhost:8001 \
  -H "Content-Type: application/json" \
  -d '{"agentId":"3613","message":{"content":"BTC"}}'
```

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/` | Get crypto snapshot for a symbol |
| `GET` | `/health` | Health check |
| `GET` | `/` | Service info |

---

## 📦 Request Format

```json
{
  "agentId": "3613",
  "message": {
    "content": "BTC"
  }
}
```

Supported symbols: `BTC`, `ETH`, `SOL`, `DOGE`, `XRP`, `ADA`, `AVAX`, `DOT`, `NEAR`, `MATIC`, and 500+ others.

---

## 📤 Response Example

```json
{
  "message": {
    "role": "assistant",
    "content": "📊 CRYPTO SNAPSHOT PRO — BTC/USDT\n\n⚡ Mild Bullish Bias\n📊 Conviction: HIGH\n🎯 Score: 3.5 LONG / 0 SHORT\n💡 Reason: Bullish factors dominate.\n\n📈 TECHNICALS..."
  }
}
```

---

## 🧠 Technical Indicators

- RSI (14)
- EMA (20, 50)
- Volume Anomaly
- Volatility (High-Low Range)
- Price vs EMA

---

## 🔧 Deployment

### Deploy to Render

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Use the following settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn server:app --host 0.0.0.0 --port 10000`

---

## ⚠️ Risk Disclosure

This service provides informational analysis based on historical and current market data. It is **NOT financial advice**. Past performance does not guarantee future results. Always do your own research and manage your risk appropriately.

---

## 📄 License

MIT

---

## 🔗 Links

- [OKX.AI Agent Profile](https://okx.ai/agents)
- [GitHub Repository](https://github.com/your-username/crypto-snapshot-pro)
- [Render Deployment](https://render.com)
