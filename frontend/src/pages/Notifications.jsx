import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Bell, Plus, Trash2, BellOff } from 'lucide-react';
import { formatPrice, formatDateTime } from '../utils/format';
import { Skeleton } from '../components/ui/Skeleton';
import toast from 'react-hot-toast';

const apiBase = '/api';
const getHeaders = () => ({ 
  'Content-Type': 'application/json',
  Authorization: `Bearer ${localStorage.getItem('access_token')}` 
});

const fetchAlerts = () => fetch(`${apiBase}/notifications/alerts`, { headers: getHeaders() }).then(r => r.json());
const fetchNotifications = () => fetch(`${apiBase}/notifications`, { headers: getHeaders() }).then(r => r.json());

const NOTIF_COLORS = {
  trade_fill: 'bg-emerald-500/20 text-emerald-400',
  price_alert: 'bg-amber-500/20 text-amber-400',
  stop_loss_trigger: 'bg-red-500/20 text-red-400',
  achievement: 'bg-violet-500/20 text-violet-400',
  system: 'bg-blue-500/20 text-blue-400',
};

export default function Notifications() {
  const qc = useQueryClient();
  const [tab, setTab] = useState('notifications');
  const [form, setForm] = useState({ symbol: '', condition: 'above', target_price: '' });

  const { data: alerts, isLoading: alertsLoading } = useQuery({ queryKey: ['alerts'], queryFn: fetchAlerts });
  const { data: notifs, isLoading: notifsLoading } = useQuery({ queryKey: ['notifications'], queryFn: fetchNotifications });

  const createAlert = useMutation({
    mutationFn: (data) => fetch(`${apiBase}/notifications/alerts`, {
      method: 'POST', headers: getHeaders(), body: JSON.stringify(data)
    }).then(r => { if (!r.ok) throw new Error(); return r.json(); }),
    onSuccess: () => { qc.invalidateQueries(['alerts']); toast.success('Alert created! 🔔'); setForm({ symbol: '', condition: 'above', target_price: '' }); },
    onError: () => toast.error('Failed to create alert'),
  });

  const deleteAlert = useMutation({
    mutationFn: (id) => fetch(`${apiBase}/notifications/alerts/${id}`, { method: 'DELETE', headers: getHeaders() }),
    onSuccess: () => { qc.invalidateQueries(['alerts']); toast.success('Alert deleted'); },
  });

  const markAllRead = useMutation({
    mutationFn: () => fetch(`${apiBase}/notifications/read-all`, { method: 'POST', headers: getHeaders() }),
    onSuccess: () => { qc.invalidateQueries(['notifications']); toast.success('All marked as read'); },
  });

  const alertList = Array.isArray(alerts) ? alerts : [];
  const notifList = Array.isArray(notifs) ? notifs : [];
  const unread = notifList.filter(n => !n.is_read).length;

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white">Notifications</h1>
          <p className="text-gray-500 text-sm">{unread > 0 ? `${unread} unread notifications` : 'All caught up!'}</p>
        </div>
        {unread > 0 && (
          <button onClick={() => markAllRead.mutate()}
            className="px-4 py-2 rounded-xl text-sm border border-white/10 bg-white/5 text-gray-400 hover:text-white transition-colors">
            Mark all read
          </button>
        )}
      </div>

      <div className="flex gap-2">
        {['notifications', 'alerts'].map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-5 py-2 rounded-xl text-sm font-medium capitalize transition-all ${
              tab === t ? 'bg-violet-600 text-white' : 'bg-white/5 border border-white/10 text-gray-400 hover:text-white'
            }`}>
            {t === 'notifications' ? <><Bell className="inline w-4 h-4 mr-1" />{t}</> : <><BellOff className="inline w-4 h-4 mr-1" />Price Alerts</>}
            {t === 'notifications' && unread > 0 && (
              <span className="ml-2 px-1.5 py-0.5 rounded-full bg-red-500 text-white text-xs font-bold">{unread}</span>
            )}
          </button>
        ))}
      </div>

      {tab === 'notifications' && (
        <div className="space-y-2">
          {notifsLoading ? (
            Array.from({length: 5}).map((_,i) => <Skeleton key={i} className="h-16 rounded-xl" />)
          ) : notifList.length === 0 ? (
            <div className="text-center py-16 text-gray-600">
              <Bell className="w-10 h-10 mx-auto mb-3 opacity-40" />
              <p>No notifications yet</p>
            </div>
          ) : notifList.map(n => (
            <div key={n.id} className={`flex items-start gap-3 p-4 rounded-xl border transition-colors ${n.is_read ? 'border-white/5 bg-white/3' : 'border-white/10 bg-white/5'}`}>
              <span className={`text-xs px-2 py-1 rounded-full font-medium flex-shrink-0 ${NOTIF_COLORS[n.notification_type] || NOTIF_COLORS.system}`}>
                {n.notification_type?.replace('_', ' ') || 'system'}
              </span>
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium ${n.is_read ? 'text-gray-400' : 'text-white'}`}>{n.title}</p>
                <p className="text-xs text-gray-600 mt-0.5">{n.message}</p>
                <p className="text-xs text-gray-700 mt-1">{formatDateTime(n.created_at)}</p>
              </div>
              {!n.is_read && <div className="w-2 h-2 rounded-full bg-violet-400 flex-shrink-0 mt-2" />}
            </div>
          ))}
        </div>
      )}

      {tab === 'alerts' && (
        <div className="space-y-4">
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-5">
            <h2 className="font-bold text-white mb-4 flex items-center gap-2">
              <Plus className="w-4 h-4" /> Create Price Alert
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
              <input
                value={form.symbol}
                onChange={e => setForm({...form, symbol: e.target.value.toUpperCase()})}
                placeholder="Symbol (e.g. AAPL)"
                className="px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white font-mono text-sm focus:border-violet-500 outline-none placeholder-gray-600"
              />
              <select
                value={form.condition}
                onChange={e => setForm({...form, condition: e.target.value})}
                className="px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-gray-300 text-sm focus:border-violet-500 outline-none"
              >
                <option value="above">Price goes above</option>
                <option value="below">Price goes below</option>
              </select>
              <input
                type="number"
                value={form.target_price}
                onChange={e => setForm({...form, target_price: e.target.value})}
                placeholder="Target price"
                className="px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white font-mono text-sm focus:border-violet-500 outline-none placeholder-gray-600"
              />
            </div>
            <button
              onClick={() => createAlert.mutate({ ...form, target_price: parseFloat(form.target_price) })}
              disabled={!form.symbol || !form.target_price || createAlert.isPending}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-cyan-600 hover:from-violet-500 hover:to-cyan-500 text-white font-semibold text-sm transition-all disabled:opacity-50"
            >
              {createAlert.isPending ? 'Creating...' : 'Create Alert'}
            </button>
          </div>

          <div className="space-y-2">
            {alertsLoading ? (
              Array.from({length: 3}).map((_,i) => <Skeleton key={i} className="h-16 rounded-xl" />)
            ) : alertList.length === 0 ? (
              <div className="text-center py-10 text-gray-600">
                <BellOff className="w-8 h-8 mx-auto mb-2 opacity-40" />
                <p className="text-sm">No active alerts</p>
              </div>
            ) : alertList.map(alert => (
              <div key={alert.id} className={`flex items-center gap-4 p-4 rounded-xl border ${alert.is_triggered ? 'border-amber-500/20 bg-amber-500/5' : 'border-white/10 bg-white/5'}`}>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-bold text-white">{alert.symbol}</span>
                    <span className="text-xs text-gray-500">
                      {alert.condition === 'above' ? '↑' : '↓'} {formatPrice(alert.target_price)}
                    </span>
                    {alert.is_triggered && <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400">Triggered</span>}
                    {!alert.is_triggered && alert.is_active && <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400">Active</span>}
                  </div>
                  {alert.notes && <p className="text-xs text-gray-600 mt-0.5">{alert.notes}</p>}
                </div>
                <button onClick={() => deleteAlert.mutate(alert.id)}
                  className="p-1.5 rounded-lg text-gray-600 hover:text-red-400 hover:bg-red-500/10 transition-colors">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}