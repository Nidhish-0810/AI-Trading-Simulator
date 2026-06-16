import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { TrendingUp, Zap, Shield, BarChart2, Brain, Trophy, ArrowRight, Activity } from 'lucide-react';

const FEATURES = [
  { icon: TrendingUp, title: 'Real Market Data', desc: 'Live prices from Yahoo Finance. 100+ stocks tracked in real-time with WebSocket updates.', color: 'from-emerald-500 to-teal-500' },
  { icon: Brain, title: 'AI Trading Signals', desc: 'RSI, MACD, Bollinger Bands combined into STRONG BUY to STRONG SELL signals with confidence scores.', color: 'from-violet-500 to-purple-500' },
  { icon: Zap, title: 'Order Matching Engine', desc: 'Market, Limit, and Stop-Loss orders with FIFO matching, partial fills, and instant confirmations.', color: 'from-yellow-500 to-orange-500' },
  { icon: BarChart2, title: 'Advanced Analytics', desc: 'Sharpe Ratio, Beta, Alpha, Max Drawdown, Win Rate and full portfolio performance analytics.', color: 'from-blue-500 to-cyan-500' },
  { icon: Shield, title: 'Risk Management', desc: 'Stop-loss orders, volatility scores, sector diversification alerts and position sizing tools.', color: 'from-red-500 to-pink-500' },
  { icon: Trophy, title: 'Gamification', desc: 'Leaderboard rankings, 15+ achievements, social trading — follow top traders and copy strategies.', color: 'from-amber-500 to-yellow-500' },
];

const STATS = [
  { label: 'Virtual Traders', value: '50,000+' },
  { label: 'Trades Executed', value: '2.4M+' },
  { label: 'Stocks Available', value: '100+' },
  { label: 'Starting Balance', value: '$100,000' },
];

const TICKER_STOCKS = [
  { symbol: 'AAPL', price: '189.25', change: '+1.24%' },
  { symbol: 'MSFT', price: '378.91', change: '+0.87%' },
  { symbol: 'NVDA', price: '875.44', change: '+3.21%' },
  { symbol: 'TSLA', price: '245.67', change: '-1.45%' },
  { symbol: 'GOOGL', price: '174.12', change: '+0.56%' },
  { symbol: 'META', price: '492.33', change: '+2.11%' },
  { symbol: 'AMZN', price: '188.78', change: '+1.03%' },
  { symbol: 'JPM', price: '198.54', change: '-0.32%' },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white overflow-hidden">
      {/* Animated gradient background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-violet-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-cyan-600/10 rounded-full blur-[120px]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-emerald-600/5 rounded-full blur-[150px]" />
      </div>

      {/* Navbar */}
      <nav className="relative z-10 border-b border-white/5 backdrop-blur-xl bg-black/20">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
              TradeAI
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/login" className="text-gray-400 hover:text-white transition-colors text-sm font-medium">
              Sign In
            </Link>
            <Link
              to="/register"
              className="px-4 py-2 rounded-lg bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-500 hover:to-cyan-500 text-white text-sm font-semibold transition-all duration-200 shadow-lg shadow-violet-500/20"
            >
              Start Trading Free
            </Link>
          </div>
        </div>
      </nav>

      {/* Ticker Tape */}
      <div className="relative z-10 border-b border-white/5 bg-black/20 overflow-hidden py-2">
        <div className="flex animate-[ticker_30s_linear_infinite] whitespace-nowrap">
          {[...TICKER_STOCKS, ...TICKER_STOCKS].map((stock, i) => (
            <div key={i} className="inline-flex items-center gap-2 px-6">
              <span className="font-mono text-xs font-bold text-white">{stock.symbol}</span>
              <span className="font-mono text-xs text-gray-400">{stock.price}</span>
              <span className={`font-mono text-xs font-medium ${stock.change.startsWith('+') ? 'text-emerald-400' : 'text-red-400'}`}>
                {stock.change}
              </span>
              <span className="text-white/10 ml-2">│</span>
            </div>
          ))}
        </div>
      </div>

      {/* Hero Section */}
      <section className="relative z-10 pt-24 pb-20 px-6">
        <div className="max-w-5xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-violet-500/30 bg-violet-500/10 text-violet-300 text-sm font-medium mb-6">
              <Zap className="w-3.5 h-3.5" />
              AI-Powered · Real Market Data · $100K Starting Balance
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="text-5xl md:text-7xl font-black leading-tight mb-6"
          >
            Trade Smarter with{' '}
            <span className="bg-gradient-to-r from-violet-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">
              AI-Powered
            </span>{' '}
            Insights
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-xl text-gray-400 max-w-3xl mx-auto mb-10 leading-relaxed"
          >
            The most advanced stock trading simulator. Real market data, AI signals,
            advanced order execution, portfolio analytics — zero risk, maximum learning.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link
              to="/register"
              className="group flex items-center gap-2 px-8 py-4 rounded-xl bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-500 hover:to-cyan-500 text-white font-bold text-lg transition-all duration-200 shadow-2xl shadow-violet-500/30 hover:shadow-violet-500/50 hover:scale-105"
            >
              Start Trading Free
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              to="/login"
              className="px-8 py-4 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 text-white font-semibold text-lg transition-all duration-200 backdrop-blur-sm"
            >
              Sign In
            </Link>
          </motion.div>
        </div>

        {/* Hero visual — animated dashboard preview */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="max-w-5xl mx-auto mt-20 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl overflow-hidden shadow-2xl shadow-black/50"
        >
          {/* Fake dashboard header */}
          <div className="border-b border-white/10 px-6 py-4 flex items-center gap-3">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <div className="w-3 h-3 rounded-full bg-yellow-500" />
              <div className="w-3 h-3 rounded-full bg-green-500" />
            </div>
            <span className="text-sm text-gray-400 font-mono">tradeai — Dashboard</span>
          </div>
          {/* Fake stat cards */}
          <div className="p-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Portfolio Value', value: '$112,847.32', change: '+12.85%', up: true },
              { label: "Day's P&L", value: '+$1,423.50', change: '+1.28%', up: true },
              { label: 'Total Return', value: '+$12,847', change: '+12.85%', up: true },
              { label: 'Cash Balance', value: '$34,210.00', change: null, up: true },
            ].map((stat, i) => (
              <div key={i} className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs text-gray-500 mb-1">{stat.label}</p>
                <p className={`font-mono text-lg font-bold ${stat.up ? 'text-emerald-400' : 'text-red-400'}`}>{stat.value}</p>
                {stat.change && (
                  <p className={`text-xs font-mono mt-0.5 ${stat.up ? 'text-emerald-400' : 'text-red-400'}`}>{stat.change}</p>
                )}
              </div>
            ))}
          </div>
          {/* Fake chart area */}
          <div className="px-6 pb-6">
            <div className="rounded-xl border border-white/10 bg-white/5 h-40 flex items-end px-4 pb-4 gap-1">
              {[40, 55, 48, 62, 58, 72, 68, 80, 75, 88, 82, 95, 90, 98, 94, 102, 97, 108].map((h, i) => (
                <div
                  key={i}
                  className="flex-1 rounded-t"
                  style={{
                    height: `${h}%`,
                    background: `linear-gradient(to top, #7c3aed, #06b6d4)`,
                    opacity: 0.7 + (i / 30),
                  }}
                />
              ))}
            </div>
          </div>
        </motion.div>
      </section>

      {/* Stats Bar */}
      <section className="relative z-10 py-10 border-y border-white/5 bg-white/2">
        <div className="max-w-5xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8">
          {STATS.map((stat, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="text-center"
            >
              <p className="text-3xl font-black bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
                {stat.value}
              </p>
              <p className="text-sm text-gray-500 mt-1">{stat.label}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Features Grid */}
      <section className="relative z-10 py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-black mb-4">Everything a Real Trader Needs</h2>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto">
              From order execution to AI analysis — a complete trading ecosystem at zero cost.
            </p>
          </motion.div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((feature, i) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                  whileHover={{ y: -4 }}
                  className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-6 hover:border-white/20 transition-all duration-300"
                >
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} p-0.5 mb-4`}>
                    <div className="w-full h-full rounded-xl bg-[#0a0a0f]/80 flex items-center justify-center">
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                  </div>
                  <h3 className="text-lg font-bold mb-2">{feature.title}</h3>
                  <p className="text-gray-400 text-sm leading-relaxed">{feature.desc}</p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative z-10 py-24 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            className="rounded-3xl border border-violet-500/30 bg-gradient-to-br from-violet-600/20 to-cyan-600/20 backdrop-blur-xl p-12"
          >
            <h2 className="text-4xl font-black mb-4">Ready to Start Trading?</h2>
            <p className="text-gray-400 mb-8 text-lg">
              Join thousands of traders. Start with $100,000 virtual balance. No credit card required.
            </p>
            <Link
              to="/register"
              className="inline-flex items-center gap-2 px-10 py-4 rounded-xl bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-500 hover:to-cyan-500 text-white font-bold text-xl transition-all duration-200 shadow-2xl shadow-violet-500/30 hover:scale-105"
            >
              Create Free Account
              <ArrowRight className="w-6 h-6" />
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 py-8 px-6 text-center text-gray-600 text-sm">
        <p>© 2024 TradeAI. Built with FastAPI, React, and real market data. For educational purposes only.</p>
      </footer>

      <style>{`
        @keyframes ticker {
          from { transform: translateX(0); }
          to { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  );
}
