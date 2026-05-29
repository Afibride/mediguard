import React, { useEffect, useState } from 'react';
import { Users, Activity, Mail, MessageSquare, ThumbsUp, Stethoscope, TrendingUp, AlertCircle } from 'lucide-react';
import { getAdminStats } from '@/services/adminApi';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

function StatCard({ icon: Icon, label, value, sub, color = 'emerald' }) {
  const colors = {
    emerald: 'text-emerald-400 bg-emerald-400/10',
    blue:    'text-blue-400 bg-blue-400/10',
    amber:   'text-amber-400 bg-amber-400/10',
    rose:    'text-rose-400 bg-rose-400/10',
    purple:  'text-purple-400 bg-purple-400/10',
  };
  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 flex items-start gap-4">
      <div className={`rounded-lg p-2.5 flex-shrink-0 ${colors[color]}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div className="min-w-0">
        <p className="text-gray-400 text-xs font-medium">{label}</p>
        <p className="text-white text-2xl font-bold mt-0.5">{value ?? '—'}</p>
        {sub && <p className="text-gray-500 text-xs mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

const DISEASE_COLORS = ['#10b981','#3b82f6','#f59e0b','#ef4444','#8b5cf6'];

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getAdminStats()
      .then(setStats)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (error) return (
    <div className="flex items-center gap-2 text-rose-400 bg-rose-950 border border-rose-800 rounded-lg p-4">
      <AlertCircle className="h-4 w-4 flex-shrink-0" />
      <span className="text-sm">{error}</span>
    </div>
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400 text-sm mt-0.5">MediGuard system overview</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        <StatCard icon={Users}       label="Total Users"         value={stats.users.total}            sub={`${stats.users.new_7d} new this week`}           color="emerald" />
        <StatCard icon={Activity}    label="Predictions"         value={stats.predictions.total}      sub={`${stats.predictions.new_7d} this week`}          color="blue"    />
        <StatCard icon={Mail}        label="Subscribers"         value={stats.newsletter.active}      sub={`of ${stats.newsletter.total} total`}             color="purple"  />
        <StatCard icon={MessageSquare} label="Unread Messages"   value={stats.messages.unread}        sub="contact inbox"                                    color="amber"   />
        <StatCard icon={ThumbsUp}    label="Satisfaction"        value={`${stats.feedback.satisfaction_pct}%`} sub={`${stats.feedback.total} ratings`}       color="emerald" />
        <StatCard icon={Stethoscope} label="Chat Conversations"  value={stats.chats.total}            sub="total AI chats"                                   color="rose"    />
      </div>

      {/* Top diseases chart */}
      {stats.top_diseases?.length > 0 && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="h-4 w-4 text-emerald-400" />
            <h2 className="text-white font-semibold text-sm">Top Predicted Diseases</h2>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={stats.top_diseases} layout="vertical" margin={{ left: 0, right: 20, top: 0, bottom: 0 }}>
              <XAxis type="number" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} width={130} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8, fontSize: 12 }}
                labelStyle={{ color: '#f3f4f6' }}
                itemStyle={{ color: '#10b981' }}
              />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {stats.top_diseases.map((_, i) => (
                  <Cell key={i} fill={DISEASE_COLORS[i % DISEASE_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
