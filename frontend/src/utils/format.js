/**
 * Utility functions for formatting prices, percentages, and numbers.
 */

/** Format a number as USD currency */
export const formatPrice = (value, decimals = 2) => {
  if (value == null || isNaN(value)) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

/** Format a percentage change */
export const formatPercent = (value, decimals = 2) => {
  if (value == null || isNaN(value)) return '0.00%';
  const formatted = Math.abs(value).toFixed(decimals);
  return `${value >= 0 ? '+' : '-'}${formatted}%`;
};

/** Format large numbers (K, M, B, T) */
export const formatNumber = (value) => {
  if (value == null || isNaN(value)) return '0';
  const abs = Math.abs(value);
  if (abs >= 1e12) return `${(value / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
  return value.toFixed(0);
};

/** Format volume */
export const formatVolume = (value) => formatNumber(value);

/** Format market cap */
export const formatMarketCap = (value) => {
  if (!value) return 'N/A';
  return formatNumber(value);
};

/** Get Tailwind color class based on value sign */
export const getChangeColor = (value) => {
  if (value > 0) return 'text-emerald-400';
  if (value < 0) return 'text-red-400';
  return 'text-gray-400';
};

/** Get gain/loss CSS color hex */
export const getChangeHex = (value) => {
  if (value > 0) return '#00d4aa';
  if (value < 0) return '#ff4757';
  return '#6b7280';
};

/** Format signal color */
export const getSignalColor = (signal) => {
  const map = {
    STRONG_BUY: '#00d4aa',
    BUY: '#10b981',
    NEUTRAL: '#6b7280',
    SELL: '#f59e0b',
    STRONG_SELL: '#ff4757',
  };
  return map[signal] || '#6b7280';
};

/** Format date */
export const formatDate = (value) => {
  if (!value) return '';
  return new Date(value).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  });
};

/** Format date + time */
export const formatDateTime = (value) => {
  if (!value) return '';
  return new Date(value).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
};

/** Clamp a value between min and max */
export const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

/** Get sector badge color */
export const getSectorColor = (sector) => {
  const map = {
    Technology: 'bg-violet-500/20 text-violet-300 border-violet-500/30',
    Healthcare: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    Finance: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    Energy: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
    Consumer: 'bg-pink-500/20 text-pink-300 border-pink-500/30',
    Industrial: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    Materials: 'bg-teal-500/20 text-teal-300 border-teal-500/30',
    Utilities: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
    Default: 'bg-gray-500/20 text-gray-300 border-gray-500/30',
  };
  return map[sector] || map.Default;
};
