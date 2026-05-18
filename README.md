# ICT Trading Dashboard

Hybrid MT5 + CSV backtesting engine with AI-powered trade journal analysis.

## Architecture

- **Backend**: FastAPI (Python) — MT5 ZeroMQ bridge, CSV loader, backtest engine (ICT Smart Money Concepts), SQLite journal, Ollama AI client
- **Frontend**: Next.js 14 — lightweight-charts candlesticks, Recharts equity curves, Tailwind dark UI
- **AI**: Local Ollama (Llama 3 / Mistral) for journal & backtest insight generation

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend proxies `/api/*` to `http://127.0.0.1:8000` via `next.config.js` rewrites.

### 3. Ollama (optional, for AI insights)

```bash
ollama serve
ollama pull llama3
```

Update `OLLAMA_MODEL` in `backend/.env` if you prefer another model.

## Data Sources

- **Live**: MT5 via ZeroMQ (requires MT5 EA running on `tcp://127.0.0.1:15555/15556`)
- **Historical**: CSV files in `backend/data/`. Sample included: `sample/eurusd_m15.csv`

## Backtest Engine

Detects ICT structures:
- **FVG** (Fair Value Gaps)
- **OB** (Order Blocks)
- **BOS/CHoCH** (Break of Structure / Change of Character)
- **Liquidity Sweeps**

Trades FVG + OB confluence with ATR-based position sizing and 1.5x SL / 2.0x TP.

## Project Structure

```
trading-dashboard/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── data.py        # CSV load, MT5 WS
│   │   │   ├── backtest.py    # Backtest run endpoint
│   │   │   ├── journal.py     # CRUD journal entries
│   │   │   └── ai.py          # Ollama insight endpoint
│   │   ├── services/
│   │   │   ├── mt5_bridge.py  # ZeroMQ client
│   │   │   ├── csv_loader.py  # CSV parser
│   │   │   ├── backtest_engine.py
│   │   │   └── ollama_client.py
│   │   ├── models/schemas.py
│   │   └── db/database.py
│   └── data/sample/eurusd_m15.csv
├── frontend/
│   ├── app/page.tsx
│   ├── components/
│   │   ├── PriceChart.tsx
│   │   ├── EquityChart.tsx
│   │   ├── BacktestPanel.tsx
│   │   ├── JournalPanel.tsx
│   │   └── AIInsightPanel.tsx
│   └── lib/api.ts
└── README.md
```
