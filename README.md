```markdown
# Crypto Snapshot Pro — A2A Endpoint for OKX.AI

**Agent ID:** #3613

Crypto Snapshot Pro is a real-time cryptocurrency technical analysis microservice built on FastAPI with A2A (Agent-to-Agent) protocol support. It provides instant, structured market snapshots for any supported crypto asset via a simple POST request.

---

## 🚀 Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/Matros777/crypto-snapshot-pro.git
cd crypto-snapshot-pro

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
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
| `GET` | `/app` | Web interface |

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
- Bollinger Bands
- MACD
- RSI Divergence
- Pivot Points

---

## 💳 Payment

Send exactly **0.025 USDC** on **Base network** to:

```
0x5b7efd37546d6BB02463339cEaDdD80997aC97B3
```

### Via x402 Protocol

```bash
# Install x402 client
npm install -g awal

# Get signal with automatic payment
awal x402 pay https://crypto-snapshot-pro.onrender.com/ \
  --method POST \
  --data '{"symbol":"ETH"}'
```

### Via Web Interface

1. Open: https://crypto-snapshot-pro.onrender.com/app
2. Connect your wallet
3. Select symbol
4. Pay 0.025 USDC
5. Get instant AI analysis

---

## 🔧 Deployment

### Deploy to Render

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Use the following settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port 10000`
4. Add environment variables:
   - `ASI_API_KEY=your-asi-api-key`
   - `ASI_MODEL=asi1`
   - `PROXY_ENABLED=false`

---

## 🛠️ Tech Stack

- **Backend:** FastAPI, Python
- **Payments:** x402 Protocol, USDC on Base
- **AI Analysis:** ASI1 API
- **Market Data:** Binance Public API
- **Frontend:** HTML, CSS, JavaScript, ethers.js

---

## 📊 Supported Symbols

BTC, ETH, BNB, XRP, SOL, DOGE, ADA, AVAX, DOT, MATIC, SHIB, LTC, UNI, LINK, ATOM, ETC, XLM, BCH, VET, FIL, ICP, HBAR, APT, ARB, NEAR, MKR, PEPE, AAVE, WIF, OP, INJ, JASMY, FLOKI, FET, THETA, MNT, RNDR, SEI, ALGO, FLOW, ENA, GALA, BEAM, GRT, EOS, QNT, KCS, BGB, XDC, IMX

**+ all other Binance USDT pairs (500+ total)**

---

## ⚠️ Risk Disclosure

This service provides informational analysis based on historical and current market data. It is **NOT financial advice**. Past performance does not guarantee future results. Always do your own research and manage your risk appropriately.

---

## 📄 License

MIT

---

## 🔗 Links

- **Web Interface:** https://crypto-snapshot-pro.onrender.com/app
- **API Endpoint:** https://crypto-snapshot-pro.onrender.com/
- **OpenX402:** https://openx402.ai/projects/0x5b7efd37546d6bb02463339ceaddd80997ac97b3
- **Full Guide:** https://gist.github.com/Matros777/c5d95532248eaaf2b86fd04f8a2753b7
- **GitHub Repository:** https://github.com/Matros777/crypto-snapshot-pro

---

## 📧 Support

- **Twitter:** https://x.com/VitalijMatros
- **GitHub Issues:** https://github.com/Matros777/crypto-snapshot-pro/issues

---

