```markdown
# Crypto Snapshot Pro

[![OpenX402](https://img.shields.io/badge/OpenX402-0x5b7e...C97B3-blue)](https://openx402.ai/projects/0x5b7efd37546d6bb02463339ceaddd80997ac97b3)
[![ClawHub](https://img.shields.io/badge/ClawHub-crypto--snapshot--pro-orange)](https://clawhub.ai/skills/crypto-snapshot-pro)

**AI-powered crypto trading signals with professional technical analysis.**

Crypto Snapshot Pro is a real-time cryptocurrency technical analysis microservice built on FastAPI with x402 payment support. It provides instant, structured market snapshots for any supported crypto asset via a simple POST request.

---

## 🚀 Quick Start

### Option 1: OVAL CLI (Recommended)

```bash
# Install OVAL
npm install -g awal

# Get a signal
npx awal x402 pay https://crypto-snapshot-pro.onrender.com/ \
  -X POST \
  -d '{"symbol":"BTC"}'
```

### Option 2: Node.js Script

#### 1. Setup

```bash
mkdir x402-pay && cd x402-pay
npm init -y
npm install @x402/fetch @x402/core @x402/evm viem
```

#### 2. Create `pay.js`

```javascript
import { wrapFetchWithPayment } from "@x402/fetch";
import { x402Client } from "@x402/core/client";
import { ExactEvmScheme } from "@x402/evm/exact/client";
import { privateKeyToAccount } from "viem/accounts";

// ============================================================
// COMMAND LINE ARGUMENTS
// ============================================================
const args = process.argv.slice(2);
let symbol = "BTC"; // Default: BTC

if (args.length > 0) {
  if (args[0].startsWith("--symbol")) {
    symbol = args[1] || "BTC";
  } else {
    symbol = args[0];
  }
}

if (args.includes("--help") || args.includes("-h")) {
  console.log(`
📊 Crypto Snapshot Pro - CLI Client

Usage:
  node pay.js [SYMBOL]
  node pay.js --symbol SYMBOL

Examples:
  node pay.js BTC
  node pay.js ETH
  node pay.js SOL
  node pay.js --symbol DOGE

Default: BTC
Price: 0.025 USDC on Base network
  `);
  process.exit(0);
}

// ============================================================
// ⚠️ IMPORTANT: INSERT YOUR PRIVATE KEY HERE
// Your wallet must have USDC on Base network
// Get it from MetaMask or any EVM wallet
// ============================================================
const PRIVATE_KEY = "0x--------------------------------------------------------------f"; // ⬅️ REPLACE WITH YOUR PRIVATE KEY

const signer = privateKeyToAccount(PRIVATE_KEY);

console.log("🔑 Wallet:", signer.address);
console.log(`📊 Symbol: ${symbol}`);

// ============================================================
// CREATE x402 CLIENT
// ============================================================
const client = new x402Client();

client.register(
  "eip155:8453",
  new ExactEvmScheme(signer)
);

// ============================================================
// DEBUG FETCH
// ============================================================
const debugFetch = async (...args) => {
  const response = await fetch(...args);

  console.log("\n📡 Status:", response.status);

  console.log("\n📨 RESPONSE HEADERS:");
  for (const [key, value] of response.headers.entries()) {
    console.log(`${key}: ${value}`);
  }

  return response;
};

// ============================================================
// x402 WRAPPER
// ============================================================
const fetch402 = wrapFetchWithPayment(
  debugFetch,
  client
);

// ============================================================
// REQUEST TO AGENT
// ============================================================
console.log(`\n📤 Sending request to agent (${symbol})...`);

const r = await fetch402(
  "https://crypto-snapshot-pro.onrender.com/",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      symbol: symbol
    })
  }
);

console.log("\n📄 Response:");
console.log(await r.text());
```

#### 3. Run

```bash
node pay.js BTC
```

### Option 3: Web Interface

1. Open: https://crypto-snapshot-pro.onrender.com/app
2. Connect your wallet
3. Select symbol
4. Pay 0.025 USDC
5. Get instant AI analysis

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/` | Get crypto signal (requires payment) |
| `POST` | `/mcp` | MCP server for AI agents (Claude, Cursor, etc.) |
| `GET` | `/health` | Health check |
| `GET` | `/` | Service info |
| `GET` | `/app` | Web interface |

---

## 🤖 MCP Integration

Crypto Snapshot Pro supports **Model Context Protocol (MCP)** for AI agents.

### Use with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "crypto-snapshot-pro": {
      "url": "https://crypto-snapshot-pro.onrender.com/mcp"
    }
  }
}
```

### Use with Cursor

```json
{
  "mcpServers": {
    "crypto-snapshot-pro": {
      "url": "https://crypto-snapshot-pro.onrender.com/mcp"
    }
  }
}
```

### Test MCP

```bash
curl -X POST https://crypto-snapshot-pro.onrender.com/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

---

## 📦 Request Format

```json
{
  "symbol": "BTC"
}
```

**Supported symbols:** BTC, ETH, SOL, DOGE, XRP, ADA, AVAX, DOT, NEAR, MATIC, and 500+ others.

---

## 📤 Response Example

```json
{
  "symbol": "BTC",
  "analysis": "📊 CRYPTO SNAPSHOT PRO — BTC/USDT\n\n🎯 TECHNICAL SIGNAL: 🚀 Strong Bullish Setup\nConviction: HIGH\nEntry: $65,100  Target: $66,800  Stop: $64,200"
}
```

---

## 💳 Payment

| Parameter | Value |
|-----------|-------|
| **Price** | 0.025 USDC |
| **Network** | Base (eip155:8453) |
| **Asset** | USDC |
| **PayTo** | `0x5b7efd37546d6BB02463339cEaDdD80997aC97B3` |
| **Timeout** | 300 seconds |

---

## 🧠 Technical Indicators

- RSI (14)
- EMA (20, 50)
- Volume Anomaly
- Bollinger Bands
- MACD
- RSI Divergence
- Pivot Points

---

## 🔧 Deployment

```bash
# Clone
git clone https://github.com/Matros777/crypto-snapshot-pro.git
cd crypto-snapshot-pro

# Install
pip install -r requirements.txt

# Run
uvicorn server:app --host 0.0.0.0 --port 10000
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `ASI_API_KEY` | ASI1 AI API key (optional) |
| `PROXY_ENABLED` | Enable proxy (true/false) |

---

## 🛠️ Tech Stack

- **Backend:** FastAPI, Python
- **Payments:** x402 Protocol, USDC on Base
- **AI Analysis:** ASI1 API
- **Market Data:** Binance Public API
- **Frontend:** HTML, CSS, JavaScript

---

## ⚠️ Risk Disclosure

This service provides informational analysis based on historical and current market data. It is **NOT financial advice**. Past performance does not guarantee future results.

---

## 🔗 Links

- **Agent:** https://crypto-snapshot-pro.onrender.com/
- **MCP Server:** https://crypto-snapshot-pro.onrender.com/mcp
- **Web Interface:** https://crypto-snapshot-pro.onrender.com/app
- **OpenX402:** https://openx402.ai/projects/0x5b7efd37546d6bb02463339ceaddd80997ac97b3
- **Full Guide:** https://gist.github.com/Matros777/c5d95532248eaaf2b86fd04f8a2753b7
- **ClawHub:** `crypto-snapshot-pro@1.0.0`
- **GitHub:** https://github.com/Matros777/crypto-snapshot-pro

---

## 📄 License

MIT

---

## 📧 Support

- **Twitter:** https://x.com/VitalijMatros
- **GitHub Issues:** https://github.com/Matros777/crypto-snapshot-pro/issues
```
