import React, { useEffect, useState, useCallback } from 'react';
import { Send, Trash2, ToggleLeft, ToggleRight, Loader2, ChevronLeft, ChevronRight, Users, Bell, CalendarClock } from 'lucide-react';
import {
  getAdminSubscribers,
  updateAdminSubscriber,
  deleteAdminSubscriber,
  sendAdminNewsletter,
  sendAdminOutbreakAlerts,
  sendAdminMonthlyDigest,
} from '@/services/adminApi';

export default function AdminNewsletter() {
  const [subs, setSubs] = useState([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [page, setPage] = useState(1);
  const [registeredCount, setRegisteredCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState(null);

  // Compose state
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState('');
  const [quickSending, setQuickSending] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getAdminSubscribers(page, 30);
      setSubs(data.subscribers);
      setTotal(data.total);
      setPages(data.pages);
      setRegisteredCount(data.registered_opted_in || 0);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => { load(); }, [load]);

  async function toggleActive(sub) {
    setActionId(sub.id + 'toggle');
    try {
      await updateAdminSubscriber(sub.id, { is_active: !sub.is_active });
      setSubs(prev => prev.map(s => s.id === sub.id ? { ...s, is_active: !s.is_active } : s));
    } catch (e) { alert(e.message); }
    finally { setActionId(null); }
  }

  async function remove(sub) {
    if (!confirm(`Remove ${sub.email} from subscribers?`)) return;
    setActionId(sub.id + 'del');
    try {
      await deleteAdminSubscriber(sub.id);
      setSubs(prev => prev.filter(s => s.id !== sub.id));
      setTotal(t => t - 1);
    } catch (e) { alert(e.message); }
    finally { setActionId(null); }
  }

  async function handleSend(e) {
    e.preventDefault();
    if (!subject.trim() || !body.trim()) return;
    if (!confirm(`Send newsletter to all active subscribers and opted-in users?`)) return;
    setSending(true);
    setSendResult('');
    try {
      const res = await sendAdminNewsletter(subject, `<p>${body.replace(/\n/g, '<br/>')}</p>`);
      setSendResult(res.message);
      setSubject('');
      setBody('');
    } catch (e) {
      setSendResult('Error: ' + e.message);
    } finally {
      setSending(false);
    }
  }

  async function handleQuickSend(type) {
    const isOutbreak = type === 'outbreak';
    if (!confirm(`Send ${isOutbreak ? 'outbreak warning emails' : 'the monthly digest'} to active subscribers and opted-in users?`)) return;
    setQuickSending(type);
    setSendResult('');
    try {
      const res = isOutbreak ? await sendAdminOutbreakAlerts() : await sendAdminMonthlyDigest();
      setSendResult(res.message);
    } catch (e) {
      setSendResult('Error: ' + e.message);
    } finally {
      setQuickSending('');
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white">Newsletter</h1>
        <p className="text-gray-400 text-sm">Manage subscribers and send newsletters</p>
      </div>

      {/* Audience summary */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {[
          { label: 'Guest Subscribers', value: total },
          { label: 'Registered Opted-in', value: registeredCount },
          { label: 'Total Reach', value: total + registeredCount },
        ].map(({ label, value }) => (
          <div key={label} className="bg-gray-900 rounded-xl border border-gray-800 p-4 flex items-center gap-3">
            <Users className="h-5 w-5 text-emerald-400 flex-shrink-0" />
            <div>
              <p className="text-gray-400 text-xs">{label}</p>
              <p className="text-white text-xl font-bold">{value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Compose */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
        <div className="flex items-center gap-2 mb-4">
          <Send className="h-4 w-4 text-emerald-400" />
          <h2 className="text-white font-semibold text-sm">Send Newsletter</h2>
        </div>
        <form onSubmit={handleSend} className="space-y-3">
          <input
            value={subject}
            onChange={e => setSubject(e.target.value)}
            placeholder="Subject line…"
            required
            className="w-full rounded-lg bg-gray-800 border border-gray-700 text-white placeholder-gray-500 px-3.5 py-2.5 text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
          />
          <textarea
            value={body}
            onChange={e => setBody(e.target.value)}
            placeholder="Newsletter body (plain text — will be auto-formatted as HTML)…"
            required
            rows={6}
            className="w-full rounded-lg bg-gray-800 border border-gray-700 text-white placeholder-gray-500 px-3.5 py-2.5 text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 resize-none"
          />
          <button
            type="submit"
            disabled={sending}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 text-white text-sm font-semibold transition"
          >
            {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            {sending ? 'Sending…' : 'Send to All'}
          </button>
        </form>
      </div>

      <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
        <div className="flex items-center gap-2 mb-4">
          <Bell className="h-4 w-4 text-orange-400" />
          <h2 className="text-white font-semibold text-sm">Admin Mail Actions</h2>
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            type="button"
            disabled={!!quickSending}
            onClick={() => handleQuickSend('outbreak')}
            className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-orange-600 hover:bg-orange-500 disabled:opacity-60 text-white text-sm font-semibold transition"
          >
            {quickSending === 'outbreak' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Bell className="h-4 w-4" />}
            Send Warning Emails
          </button>
          <button
            type="button"
            disabled={!!quickSending}
            onClick={() => handleQuickSend('digest')}
            className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-60 text-white text-sm font-semibold transition"
          >
            {quickSending === 'digest' ? <Loader2 className="h-4 w-4 animate-spin" /> : <CalendarClock className="h-4 w-4" />}
            Send Monthly Digest
          </button>
        </div>
      </div>

      {sendResult && (
        <div className={`rounded-lg px-3 py-2 text-xs border ${sendResult.startsWith('Error') ? 'bg-rose-950 border-rose-700 text-rose-300' : 'bg-emerald-950 border-emerald-700 text-emerald-300'}`}>
          {sendResult}
        </div>
      )}

      {/* Subscriber list */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-800">
          <h2 className="text-white font-semibold text-sm">Guest Subscribers ({total})</h2>
        </div>
        {loading ? (
          <div className="flex items-center justify-center h-40"><Loader2 className="h-6 w-6 text-emerald-400 animate-spin" /></div>
        ) : subs.length === 0 ? (
          <div className="text-center text-gray-500 py-12 text-sm">No subscribers yet</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800">
                  {['Email / Name', 'Status', 'Subscribed', 'Actions'].map(h => (
                    <th key={h} className="text-left text-xs text-gray-500 font-medium px-4 py-3">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {subs.map(s => (
                  <tr key={s.id} className="hover:bg-gray-800/40 transition-colors">
                    <td className="px-4 py-3">
                      <p className="text-white">{s.email}</p>
                      <p className="text-gray-500 text-xs">{s.name}</p>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium border ${s.is_active ? 'bg-emerald-900/50 text-emerald-300 border-emerald-700' : 'bg-gray-800 text-gray-500 border-gray-700'}`}>
                        {s.is_active ? 'Active' : 'Unsubscribed'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs">
                      {s.subscribed_at ? new Date(s.subscribed_at).toLocaleDateString() : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <button onClick={() => toggleActive(s)} disabled={!!actionId} title={s.is_active ? 'Unsubscribe' : 'Re-subscribe'}
                          className="p-1.5 rounded hover:bg-gray-700 text-gray-400 hover:text-white transition disabled:opacity-40">
                          {actionId === s.id + 'toggle' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : s.is_active ? <ToggleRight className="h-3.5 w-3.5 text-emerald-400" /> : <ToggleLeft className="h-3.5 w-3.5" />}
                        </button>
                        <button onClick={() => remove(s)} disabled={!!actionId} title="Remove"
                          className="p-1.5 rounded hover:bg-rose-950 text-gray-500 hover:text-rose-400 transition disabled:opacity-40">
                          {actionId === s.id + 'del' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {pages > 1 && (
        <div className="flex items-center justify-end gap-2 text-sm">
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
            className="p-1.5 rounded-lg bg-gray-800 border border-gray-700 text-gray-300 hover:bg-gray-700 disabled:opacity-40">
            <ChevronLeft className="h-4 w-4" />
          </button>
          <span className="text-gray-500 text-xs">Page {page} of {pages}</span>
          <button disabled={page >= pages} onClick={() => setPage(p => p + 1)}
            className="p-1.5 rounded-lg bg-gray-800 border border-gray-700 text-gray-300 hover:bg-gray-700 disabled:opacity-40">
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}
