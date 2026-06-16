import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Trophy, Medal, Crown, TrendingUp } from 'lucide-react';
import { portfolioService } from '../services/portfolio.service';
import { formatPrice, formatPercent, getChangeColor } from '../utils/format';
import { useAuthStore } from '../store/authStore';
import { Skeleton } from '../components/ui/Skeleton';

const RANK_STYLES = {
  1: { icon: Crown, color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/30' },
  2: { icon: Medal, color: 'text-gray-300', bg: 'bg-gray-500/10 border-gray-500/30' },
  3: { icon: Medal, color: 'text-amber-600', bg: 'bg-amber-800/10 border-amber-800/30' },
};

const ACHIEVEMENTS = [
  { type: 'first_trade', title: 'First Blood', icon: '⚡', desc: 'First trade' },
  { type: 'ten_trades', title: 'Active Trader', icon: '🔥', desc: '10 trades' },
  { type: 'fifty_trades', title: 'Speed Trader', icon: '🚀', desc: '50 trades' },
  { type: 'profit_10pct', title: 'In The Green', icon: '📈', desc: '+10% return' },
  { type: 'profit_25pct', title: 'Strong Performer', icon: '💰', desc: '+25% return' },
  { type: 'profit_50pct', title: 'Half-Century', icon: '🏆', desc: '+50% return' },
  { type: 'profit_100pct', title: 'Doubler', icon: '👑', desc: 'Portfolio doubled' },
  { type: 'diversified_5', title: 'Diversified', icon: '🎯', desc: '5 stocks held' },
  { type: 'high_roller', title: 'High Roller', icon: '💎', desc: 'Portfolio >$150K' },
];

export default function Leaderboard() {
  const { user } = useAuthStore();
  const [tab, setTab] = useState('leaderboard');

  const { data: leaderboard, isLoading: lbLoading } = useQuery({
    queryKey: ['leaderboard'],
    queryFn: () => fetch('/api/leaderboard', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    }).then(r => r.json()),
    refetchInterval: 60000,
  });

  const { data: achievements, isLoading: achLoading } = useQuery({
    queryKey: ['achievements'],
    queryFn: () => fetch('/api/achievements', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    }).then(r => r.json()),
    enabled: tab === 'achievements',
  });

  const leaders = Array.isArray(leaderboard) ? leaderboard : leaderboard?.leaderboard || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-black text-white">Leaderboard</h1>
        <p className="text-gray-500 text-sm">Top traders ranked by portfolio return</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        {['leaderboard', 'achievements'].map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-5 py-2 rounded-xl text-sm font-medium capitalize transition-all ${
              tab === t ? 'bg-violet-600 text-white shadow-lg shadow-violet-500/20' : 'bg-white/5 border border-white/10 text-gray-400 hover:text-white'
            }`}>
            {t === 'leaderboard' ? <><Trophy className="inline w-4 h-4 mr-1.5" />Leaderboard</> : '🏆 Achievements'}
          </button>
        ))}
      </div>

      {tab === 'leaderboard' && (
        <>
          {/* Top 3 podium */}
          {!lbLoading && leaders.length >= 3 && (
            <div className="grid grid-cols-3 gap-4">
              {[leaders[1], leaders[0], leaders[2]].map((trader, podiumPos) => {
                if (!trader) return <div key={podiumPos} />;
                const rank = trader.rank;
                const style = RANK_STYLES[rank] || {};
                const Icon = style.icon || Trophy;
                return (
                  <div key={rank} className={`rounded-2xl border p-5 text-center ${style.bg || 'border-white/10 bg-white/5'} ${podiumPos === 1 ? 'ring-2 ring-yellow-500/30' : ''}`}>
                    <Icon className={`w-8 h-8 mx-auto mb-2 ${style.color || 'text-gray-400'}`} />
                    <div className="w-12 h-12 mx-auto mb-2 rounded-full bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center text-xl font-black">
                      {trader.username?.[0]?.toUpperCase()}
                    </div>
                    <p className="font-bold text-white text-sm">{trader.username}</p>
                    <p className={`font-mono text-lg font-black mt-1 ${getChangeColor(trader.total_return_pct)}`}>
                      {formatPercent(trader.total_return_pct)}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">{formatPrice(trader.portfolio_value)}</p>
                    <div className={`text-xs mt-2 font-bold ${style.color}`}>#{rank}</div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Full Table */}
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm overflow-hidden">
            <div className="grid grid-cols-[48px_1fr_120px_120px_80px] gap-x-4 px-5 py-3 border-b border-white/10 text-xs text-gray-500 font-medium">
              <span>Rank</span>
              <span>Trader</span>
              <span className="text-right">Portfolio</span>
              <span className="text-right">Return</span>
              <span className="text-right">Trades</span>
            </div>
            {lbLoading ? (
              <div className="p-5 space-y-3">{Array.from({length: 10}).map((_,i) => <Skeleton key={i} className="h-12" />)}</div>
            ) : leaders.map(trader => (
              <div key={trader.user_id}
                className={`grid grid-cols-[48px_1fr_120px_120px_80px] gap-x-4 px-5 py-3.5 border-b border-white/5 hover:bg-white/5 transition-colors items-center ${trader.is_current_user ? 'bg-violet-500/5 border-violet-500/20' : ''}`}>
                <div className="text-center">
                  {RANK_STYLES[trader.rank] ? (
                    React.createElement(RANK_STYLES[trader.rank].icon, { className: `w-5 h-5 ${RANK_STYLES[trader.rank].color}` })
                  ) : (
                    <span className="font-mono text-sm text-gray-500">#{trader.rank}</span>
                  )}
                </div>
                <div className="flex items-center gap-2 min-w-0">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center text-xs font-black flex-shrink-0">
                    {trader.username?.[0]?.toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <p className={`text-sm font-semibold truncate ${trader.is_current_user ? 'text-violet-300' : 'text-white'}`}>
                      {trader.username} {trader.is_current_user && <span className="text-xs text-violet-400">(you)</span>}
                    </p>
                    <p className="text-xs text-gray-600 truncate">{trader.full_name}</p>
                  </div>
                </div>
                <p className="text-right font-mono text-sm text-white">{formatPrice(trader.portfolio_value)}</p>
                <p className={`text-right font-mono text-sm font-bold ${getChangeColor(trader.total_return_pct)}`}>
                  {formatPercent(trader.total_return_pct)}
                </p>
                <p className="text-right font-mono text-sm text-gray-400">{trader.total_trades}</p>
              </div>
            ))}
          </div>
        </>
      )}

      {tab === 'achievements' && (
        <div className="space-y-4">
          {achLoading ? (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {Array.from({length: 9}).map((_,i) => <Skeleton key={i} className="h-32 rounded-2xl" />)}
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between">
                <p className="text-gray-500 text-sm">
                  {achievements?.earned_count || 0}/{achievements?.total_count || 0} earned • {achievements?.total_xp || 0} XP
                </p>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {(achievements?.achievements || ACHIEVEMENTS).map((ach) => (
                  <div key={ach.achievement_type}
                    className={`rounded-2xl border p-4 transition-all ${ach.earned ? 'border-violet-500/40 bg-violet-500/10' : 'border-white/10 bg-white/5 opacity-50'}`}>
                    <div className="text-3xl mb-2">{ach.icon}</div>
                    <p className={`font-bold text-sm ${ach.earned ? 'text-white' : 'text-gray-600'}`}>{ach.title}</p>
                    <p className="text-xs text-gray-600 mt-0.5">{ach.description || ach.desc}</p>
                    {ach.earned && ach.earned_at && (
                      <p className="text-xs text-violet-400 mt-2">
                        ✓ {new Date(ach.earned_at).toLocaleDateString()}
                      </p>
                    )}
                    {!ach.earned && <p className="text-xs text-gray-700 mt-2">🔒 Locked</p>}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

import React from 'react';
