import { useState } from 'react';
import { formatPrice, formatDateTime } from '../../utils/format';

const TYPE_COLORS = {
  buy: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  sell: 'bg-red-500/20 text-red-400 border-red-500/30',
  commission: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  deposit: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  withdrawal: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
};

export default function TransactionHistory({ transactions = [] }) {
  const [filter, setFilter] = useState('all');

  const filtered = transactions.filter(t => {
    if (filter === 'all') return true;
    return t.transaction_type === filter;
  });

  if (transactions.length === 0) {
    return <p className="text-center text-gray-600 py-8 text-sm">No transactions yet</p>;
  }

  return (
    <div>
      {/* Filter */}
      <div className="flex gap-2 mb-4 overflow-x-auto">
        {['all', 'buy', 'sell', 'commission'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-3 py-1 rounded-lg text-xs font-medium capitalize transition-all ${
              filter === f ? 'bg-violet-600 text-white' : 'bg-white/5 border border-white/10 text-gray-500 hover:text-white'
            }`}>
            {f}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10 text-xs text-gray-500">
              <th className="py-2 text-left">Date</th>
              <th className="py-2 text-left">Type</th>
              <th className="py-2 text-left">Symbol</th>
              <th className="py-2 text-right">Qty</th>
              <th className="py-2 text-right">Price</th>
              <th className="py-2 text-right">Amount</th>
              <th className="py-2 text-right">Balance</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {filtered.slice(0, 50).map((t, i) => (
              <tr key={t.id || i} className="hover:bg-white/5 transition-colors">
                <td className="py-2 text-xs text-gray-500 font-mono">{formatDateTime(t.created_at)}</td>
                <td className="py-2">
                  <span className={`px-2 py-0.5 rounded-full text-xs border ${TYPE_COLORS[t.transaction_type] || 'bg-gray-500/20 text-gray-400 border-gray-500/30'}`}>
                    {t.transaction_type?.toUpperCase()}
                  </span>
                </td>
                <td className="py-2 font-mono text-white text-sm">{t.symbol || '—'}</td>
                <td className="py-2 text-right font-mono text-gray-300 text-xs">{t.quantity?.toFixed(4) || '—'}</td>
                <td className="py-2 text-right font-mono text-gray-300 text-xs">{t.price ? formatPrice(t.price) : '—'}</td>
                <td className={`py-2 text-right font-mono text-xs ${t.transaction_type === 'buy' || t.transaction_type === 'commission' ? 'text-red-400' : 'text-emerald-400'}`}>
                  {t.transaction_type === 'buy' || t.transaction_type === 'commission' ? '-' : '+'}{formatPrice(t.total_amount)}
                </td>
                <td className="py-2 text-right font-mono text-gray-400 text-xs">{formatPrice(t.balance_after)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
