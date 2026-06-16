# 🤖 AI-Powered Stock Trading Simulator

<div align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" />
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/yfinance-239120?style=for-the-badge&logo=yahoo&logoColor=white" />
</div>

<br/>

A **full-stack, production-grade** stock trading simulator with real market data, AI-powered signals, advanced portfolio analytics, and WebSocket live updates — **zero paid APIs required**.

---

## ✨ Features

### 📊 Real Market Data
- Live stock quotes via **yfinance** (100+ stocks across all sectors)
- OHLCV candlestick charts with multiple timeframes (1D, 1W, 1M, 1Y)
- Market indices: S&P 500, NASDAQ, DOW, VIX
- Top gainers, losers, and most-active stocks
- Stock news and watchlist

### 🤖 AI Trading Signals (No OpenAI required)
- **RSI** — Relative Strength Index (oversold/overbought detection)
- **MACD** — Moving Average Convergence Divergence crossovers
- **Bollinger Bands** — Mean reversion squeeze detection  
- **SMA 50/200** — Golden Cross / Death Cross detection
- **Stochastic Oscillator** — Momentum confirmation
- Combined signal: `STRONG_BUY | BUY | NEUTRAL | SELL | STRONG_SELL`
- News sentiment analysis (keyword-based NLP)

### 📈 Portfolio Analytics
- **Sharpe Ratio** — Risk-adjusted returns
- **Beta** — Correlation with S&P 500
- **Alpha** — Jensen's Alpha (annualized)
- **Max Drawdown** — Peak-to-trough decline
- **Win Rate** — % of profitable trades
- **Sector Allocation** — Pie chart breakdown
- Portfolio value history chart

### ⚡ Order Engine
- Market orders (instant execution)
- Limit orders (FIFO matching)
- Stop-loss orders
- 0.1% commission per trade
- Real-time balance updates

### 🎯 Backtesting Engine
- 4 built-in strategies: SMA Crossover, RSI, MACD, Bollinger Bands
- Custom date ranges and starting capital
- Equity curve visualization
- Trade-by-trade breakdown

### 🏆 Social Features
- Leaderboard ranked by portfolio ROI
- 15 achievement badges
- Follow other traders

### 🔴 Live Updates
- WebSocket price feed (5-second updates)
- Personal notification channel (order fills, price alerts)
- Redis pub/sub for real-time broadcasting

---

## 🗂️ Project Structure

```
AI-Trading-Simulator/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── ai/                 # Signals, sentiment, backtesting, indicators
│   │   ├── auth/               # JWT auth, user management
│   │   ├── core/               # Config, DB, Redis, security, exceptions
│   │   ├── leaderboard/        # Rankings, achievements, social
│   │   ├── market/             # yfinance client, quotes, history, news
│   │   ├── notifications/      # Price alerts, notification history
│   │   ├── portfolio/          # Holdings, analytics, transactions
│   │   ├── trading/            # Order engine, trade execution
│   │   └── websocket/          # WebSocket manager, price feed
│   ├── alembic/                # Database migrations
│   ├── tests/                  # pytest test suite
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/                   # React + Vite + Tailwind CSS
│   ├── src/
│   │   ├── components/         # UI, charts, trading, portfolio, AI widgets
│   │   ├── hooks/              # useWebSocket, useDebounce, usePageTitle
│   │   ├── pages/              # 11 pages (Dashboard, Markets, Portfolio...)
│   │   ├── services/           # API service layer (auth, market, trading, AI)
│   │   ├── store/              # Zustand stores (auth, market, portfolio)
│   │   └── utils/              # Format helpers
│   ├── Dockerfile
│   └── vite.config.js
├── nginx/                      # Reverse proxy config
│   └── nginx.conf
├── docker-compose.yml          # Full stack orchestration
├── render.yaml                 # One-click Render.com deployment
└── .env.example                # Environment variable template
```

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# 1. Clone
git clone https://github.com/Nidhish-0810/AI-Trading-Simulator.git
cd AI-Trading-Simulator

# 2. Configure environment
cp .env.example .env
# Edit .env — generate a SECRET_KEY:
python -c "import secrets; print(secrets.token_hex(32))"

# 3. Start all services
docker-compose up --build

# App:      http://localhost:3000
# API docs: http://localhost:8000/docs
```

### Option 2: Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start PostgreSQL + Redis (or use Docker for just those):
docker run -d -e POSTGRES_USER=tradeai -e POSTGRES_PASSWORD=tradeai_secret_2024 -e POSTGRES_DB=tradeai_db -p 5432:5432 postgres:16-alpine
docker run -d --requirepass redis_secret_2024 -p 6379:6379 redis:7-alpine

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## 🌐 Deploy to Render.com

1. Push to GitHub
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect this repository
4. Render auto-detects `render.yaml` and creates all services
5. Set `SECRET_KEY` in the backend service environment variables

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS, Zustand, React Query |
| Charts | Recharts, custom OHLCV candlestick |
| Animation | Framer Motion |
| Backend | FastAPI (async), Python 3.11 |
| Database | PostgreSQL 16 + SQLAlchemy async |
| Cache | Redis 7 (caching + pub/sub) |
| Auth | JWT (access + refresh tokens) |
| Market Data | yfinance (free, no API key) |
| AI/ML | Custom technical analysis (ta library) |
| DevOps | Docker, docker-compose, GitHub Actions |
| Deployment | Render.com |

---

## 📡 API Reference

Full interactive docs available at `http://localhost:8000/docs` (Swagger UI).

Key endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Login → JWT tokens |
| GET | `/api/market/stock/{symbol}` | Real-time quote |
| GET | `/api/market/stock/{symbol}/history` | OHLCV data |
| GET | `/api/market/gainers` | Top gaining stocks |
| POST | `/api/trading/order` | Place order |
| GET | `/api/portfolio` | Holdings + P&L |
| GET | `/api/portfolio/analytics` | Sharpe, Beta, Alpha |
| GET | `/api/ai/signals/{symbol}` | AI trading signal |
| POST | `/api/ai/backtest` | Run backtest |
| WS | `/ws/prices` | Live price feed |

---

## 🔐 Environment Variables

See [`.env.example`](.env.example) for all required variables.

Critical ones:
```env
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=redis://:password@host:6379/0
STARTING_BALANCE=100000.0
```

---

## 📝 License

MIT License — see [LICENSE](LICENSE)

---

<div align="center">
  Built with ❤️ by <a href="https://github.com/Nidhish-0810">Nidhish Suvarna</a>
</div>
