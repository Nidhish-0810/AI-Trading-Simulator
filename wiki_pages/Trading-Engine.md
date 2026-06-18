# Trading Engine

The core of the AI Trading Simulator is a custom-built, highly concurrent order matching and execution engine located in `app.trading.order_engine`.

## 📈 Supported Order Types

1. **Market Orders**
   - Executed immediately at the best available current market price fetched from `yfinance`.
   - Guaranteed execution (if sufficient funds/shares exist), but the final price is subject to slippage.

2. **Limit Orders**
   - Placed in the virtual Order Book.
   - **Buy Limit**: Only executes if the market price falls to or below the limit price.
   - **Sell Limit**: Only executes if the market price rises to or above the limit price.

3. **Stop-Loss Orders**
   - Used to mitigate risk. Triggers a Market Sell order automatically if the price drops below the defined stop price.

## ⚙️ Matching Engine Logic

The engine does not match users against users (as this is a simulator). Instead, it matches users against the real-world market using live data.

### Limit Order Matching (`match_limit_orders`)
A background task runs periodically to check all pending limit orders against the current market price.
- **FIFO (First-In-First-Out)**: Orders placed earlier are prioritized.
- **Partial Fills**: If an order cannot be entirely filled (simulating low volume, though currently volume constraints are relaxed for UX), the engine updates the `filled_quantity` and keeps the order `status` as `partial`.
- **Commissions**: A flat 0.1% simulated broker fee is deducted from the `balance` during execution.

### Validations & Safety
Before any order is placed, the engine runs strict cryptographic and financial checks:
- **Insufficient Funds Check**: Calculates total cost (Quantity × Price + Commission). If it exceeds the user's `balance`, an `InsufficientFundsError` is thrown.
- **Insufficient Shares Check**: For sell orders, ensures the user actually owns the exact amount of shares in their `Holdings` table.

## 📊 Portfolio Analytics

When an order executes, it updates the user's `Holding` and `Transaction` ledgers. The `portfolio.analytics` module provides advanced financial metrics:

- **Sharpe Ratio**: Measures risk-adjusted return. Calculated using the annualized standard deviation of daily portfolio returns against a risk-free rate (default 5%).
- **Beta**: Measures the portfolio's volatility against the broader market (S&P 500).
- **Max Drawdown**: Calculates the largest single drop in portfolio value from peak to trough.
- **Sector Allocation**: Maps held symbols to their respective industry sectors to visualize portfolio diversification.
