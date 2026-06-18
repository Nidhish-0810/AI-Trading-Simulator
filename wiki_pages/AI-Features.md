# AI & Analytics Features

The "AI" in AI Trading Simulator comes from a robust suite of algorithmic indicators, sentiment scrapers, and signal generators designed to give traders an edge.

## 📉 Technical Indicators (`app.ai.indicators`)

We use `pandas` and vector math to calculate industry-standard technical indicators on the fly. 

- **RSI (Relative Strength Index)**: Identifies overbought (>70) or oversold (<30) conditions.
- **MACD (Moving Average Convergence Divergence)**: Tracks momentum via the relationship between two moving averages.
- **Bollinger Bands**: Measures volatility and potential price breakouts by plotting standard deviations around an SMA.
- **SMA & EMA**: Simple and Exponential Moving averages used to identify long-term trends.
- **ATR & OBV**: Average True Range (volatility) and On-Balance Volume (buying/selling pressure).

## 🤖 Signal Generation (`app.ai.signals`)

The signal generator is a deterministic scoring algorithm that aggregates the outputs of the technical indicators.

### The Scoring Matrix
When a user requests an AI analysis, the system fetches the last 1 year of daily OHLCV data. It calculates the indicators and assigns points:
- **RSI**: +2 points if oversold (Bullish), -2 points if overbought (Bearish).
- **MACD**: +2 points for a bullish crossover, -2 for bearish.
- **Moving Averages**: +1 point if the current price is above the 50-day SMA.

### The Output
The sum of these points is mapped to a human-readable signal:
- `> 3`: **STRONG BUY**
- `1 to 3`: **BUY**
- `0`: **NEUTRAL**
- `-1 to -3`: **SELL**
- `< -3`: **STRONG SELL**

The API also returns an array of "Reasoning" strings (e.g., *"RSI is oversold at 28.5, indicating a potential reversal."*) which the frontend displays to the user.

## 📰 News Sentiment Analysis (`app.ai.sentiment`)

The sentiment engine scrapes recent financial news headlines for a specific stock ticker using `yfinance`'s news feed.

### Lexicon-Based Scoring
Instead of relying on heavy LLMs, the engine uses a highly optimized, financial-specific lexicon:
- **Positive Keywords**: "surge", "rally", "earnings beat", "acquisition", "dividend".
- **Negative Keywords**: "lawsuit", "fraud", "miss", "downgrade", "layoffs", "crash".

The text is tokenized, scored, and normalized between `-1.0` (Extremely Bearish) and `1.0` (Extremely Bullish).

## ⏱ Backtesting Engine (`app.ai.backtesting`)

Users can test hypothetical strategies on historical data before risking simulated money.
- **How it works**: The user inputs a symbol, a timeframe, and a strategy (e.g., "SMA Crossover"). The engine iterates chronologically through historical data, triggering virtual buys and sells based *only* on data available at that specific timestamp (preventing lookahead bias).
- **Output**: Returns total return %, win rate, and an equity curve chart that the frontend graphs via Chart.js/Recharts.
