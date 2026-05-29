import React, { useEffect, useState } from 'react';
import { TrendingUp, Loader2 } from 'lucide-react';
import { getAdminTrends } from '@/services/adminApi';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

const COLORS = ['#10b981','#3b82f6','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#f97316','#a3e635','#e879f9','#fb7185'];

const DAYS_OPTIONS = [7, 14, 30, 90];

export default function AdminTrends() {
  const [days, setDays] = useState(30);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getAdminTrends(days)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [days]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-white">Trends & Analytics</h1>
          <p className="text-gray-400 text-sm">Prediction and usage statistics</p>
        </div>
        <div className="flex gap-1.5">
          {DAYS_OPTIONS.map(d => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                days === d
                  ? 'bg-emerald-600 border-emerald-600 text-white'
                  : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-emerald-500 hover:text-white'
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-7 w-7 text-emerald-400 animate-spin" />
        </div>
      ) : !data ? (
        <div className="text-center text-gray-500 py-16">No data available</div>
      ) : (
        <>
          {/* Daily predictions area chart */}
          {data.daily_predictions.length > 0 && (
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
              <h2 className="text-white font-semibold text-sm mb-4 flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-emerald-400" /> Daily Predictions
              </h2>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={data.daily_predictions}>
                  <defs>
                    <linearGradient id="gp" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="day" tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8, fontSize: 12 }} labelStyle={{ color: '#f3f4f6' }} itemStyle={{ color: '#10b981' }} />
                  <Area type="monotone" dataKey="count" stroke="#10b981" strokeWidth={2} fill="url(#gp)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-4">
            {/* Disease distribution */}
            {data.disease_distribution.length > 0 && (
              <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
                <h2 className="text-white font-semibold text-sm mb-4">Top Diseases</h2>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={data.disease_distribution} layout="vertical">
                    <XAxis type="number" tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} />
                    <YAxis type="category" dataKey="name" width={120} tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8, fontSize: 12 }} labelStyle={{ color: '#f3f4f6' }} />
                    <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                      {data.disease_distribution.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Feedback pie */}
            {(data.feedback.helpful + data.feedback.not_helpful) > 0 && (
              <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
                <h2 className="text-white font-semibold text-sm mb-4">Chat Feedback</h2>
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Helpful', value: data.feedback.helpful },
                        { name: 'Not helpful', value: data.feedback.not_helpful },
                      ]}
                      cx="50%" cy="50%" innerRadius={55} outerRadius={80}
                      dataKey="value" paddingAngle={3}
                    >
                      <Cell fill="#10b981" />
                      <Cell fill="#ef4444" />
                    </Pie>
                    <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8, fontSize: 12 }} />
                    <Legend iconType="circle" iconSize={8} formatter={v => <span className="text-gray-400 text-xs">{v}</span>} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Age distribution */}
          {data.age_distribution.length > 0 && (
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
              <h2 className="text-white font-semibold text-sm mb-4">Age Distribution</h2>
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={data.age_distribution}>
                  <XAxis dataKey="group" tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8, fontSize: 12 }} />
                  <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  );
}
