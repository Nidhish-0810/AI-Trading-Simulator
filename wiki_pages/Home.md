# Welcome to AI Trading Simulator

Welcome to the **AI Trading Simulator** Wiki! This project is a fully functional, highly scalable stock market simulation platform equipped with advanced AI-driven features. It allows users to trade stocks in a risk-free environment, backtest strategies, and leverage AI to make informed trading decisions.

## 🚀 Key Features

### 1. Robust Trading Engine
- **Order Types**: Support for Market Orders, Limit Orders, and Stop-Loss Orders.
- **Matching Engine**: FIFO-based partial fill matching engine simulation.
- **Live Market Data**: Integrates seamlessly with `yfinance` to fetch real-time and historical stock data.
- **Portfolio Analytics**: Deep insights including Sharpe Ratio, Beta, Alpha, and Maximum Drawdown.

### 2. AI & Technical Analysis
- **Technical Indicators**: RSI, MACD, Bollinger Bands, SMA, EMA, and more calculated on the fly.
- **Signal Generation**: AI-driven "Strong Buy", "Buy", "Neutral", "Sell", "Strong Sell" signals based on weighted indicator scores.
- **Sentiment Analysis**: Analyzes financial news headlines to derive positive, negative, or neutral sentiment scores.
- **Backtesting Platform**: Run historical backtests using custom strategies (e.g., SMA Crossover, RSI Oversold).

### 3. Beautiful UI / UX
- **Glassmorphism Aesthetics**: Built with React, Vite, and Tailwind CSS for a premium, modern feel.
- **Real-time Updates**: WebSockets provide live price feeds and instant notification alerts.
- **Interactive Charts**: Dynamic stock charts for deep technical analysis.

### 4. Enterprise-Grade CI/CD
- **Automated Testing**: 100% robust Pytest suite using transactional rollbacks and in-memory databases.
- **Dockerized Environments**: Consistent deployment from local dev to production.
- **GitHub Actions**: Fully automated pipelines for linting, testing, building Docker images, and deploying to Render.

## 📖 How to Navigate this Wiki

Use the sidebar on the right to navigate through the detailed documentation:

- **[Architecture](Architecture)**: Learn about the Tech Stack and how the frontend, backend, and databases interact.
- **[Setup & Installation](Setup-and-Installation)**: Get the project running locally using Docker or manual installation.
- **[Trading Engine](Trading-Engine)**: Deep dive into how orders are matched and executed.
- **[AI Features](AI-Features)**: Understand the math and logic behind our AI signals and sentiment analysis.
- **[CI/CD Pipeline](CI-CD-Pipeline)**: Explore our robust automated deployment and testing strategies.

---
*Ready to start? Head over to the [Setup and Installation](Setup-and-Installation) guide!*
