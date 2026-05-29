import React, { useEffect, useState, useCallback } from 'react';
import { Mail, MailOpen, Trash2, Loader2, ChevronLeft, ChevronRight, Filter } from 'lucide-react';
import { getAdminMessages, markMessageRead, deleteAdminMessage } from '@/services/adminApi';

export default function AdminMessages() {
  const [messages, setMessages] = useState([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [page, setPage] = useState(1);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState(null);
  const [expanded, setExpanded] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getAdminMessages(page, 20, unreadOnly);
      setMessages(data.messages);
      setTotal(data.total);
      setPages(data.pages);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [page, unreadOnly]);

  useEffect(() => { load(); }, [load]);

  async function markRead(id) {
    setActionId(id + 'read');
    try {
      await markMessageRead(id);
      setMessages(prev => prev.map(m => m.id === id ? { ...m, read: true, read_at: new Date().toISOString() } : m));
    } catch (e) { alert(e.message); }
    finally { setActionId(null); }
  }

  async function remove(id) {
    if (!confirm('Delete this message?')) return;
    setActionId(id + 'del');
    try {
      await deleteAdminMessage(id);
      setMessages(prev => prev.filter(m => m.id !== id));
      setTotal(t => t - 1);
    } catch (e) { alert(e.message); }
    finally { setActionId(null); }
  }

  function toggleExpand(id) {
    setExpanded(e => e === id ? null : id);
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-white">Contact Messages</h1>
          <p className="text-gray-400 text-sm">{total} {unreadOnly ? 'unread' : 'total'} messages</p>
        </div>
        <button
          onClick={() => { setUnreadOnly(v => !v); setPage(1); }}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm border transition ${unreadOnly ? 'bg-emerald-600 border-emerald-600 text-white' : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-emerald-500 hover:text-white'}`}
        >
          <Filter className="h-3.5 w-3.5" />
          {unreadOnly ? 'Unread only' : 'All messages'}
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48"><Loader2 className="h-6 w-6 text-emerald-400 animate-spin" /></div>
      ) : messages.length === 0 ? (
        <div className="bg-gray-900 rounded-xl border border-gray-800 py-16 text-center text-gray-500 text-sm">
          No messages found
        </div>
      ) : (
        <div className="space-y-2">
          {messages.map(m => (
            <div
              key={m.id}
              className={`bg-gray-900 rounded-xl border transition-colors ${m.read ? 'border-gray-800' : 'border-emerald-700/50'}`}
            >
              {/* Header row */}
              <div
                className="flex items-start gap-3 px-4 py-3.5 cursor-pointer"
                onClick={() => { toggleExpand(m.id); if (!m.read) markRead(m.id); }}
              >
                <div className={`mt-0.5 flex-shrink-0 ${m.read ? 'text-gray-600' : 'text-emerald-400'}`}>
                  {m.read ? <MailOpen className="h-4 w-4" /> : <Mail className="h-4 w-4" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`font-medium text-sm ${m.read ? 'text-gray-300' : 'text-white'}`}>{m.name}</span>
                    <span className="text-gray-500 text-xs">{m.email}</span>
                    {!m.read && <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-600 text-white uppercase tracking-wide">New</span>}
                  </div>
                  <p className={`text-sm mt-0.5 truncate ${m.read ? 'text-gray-400' : 'text-gray-200'}`}>{m.subject}</p>
                  {expanded !== m.id && (
                    <p className="text-gray-500 text-xs mt-1 line-clamp-1">{m.message}</p>
                  )}
                </div>
                <span className="text-gray-600 text-[10px] flex-shrink-0 pt-0.5">
                  {m.sent_at ? new Date(m.sent_at).toLocaleDateString() : ''}
                </span>
              </div>

              {/* Expanded message body */}
              {expanded === m.id && (
                <div className="px-4 pb-4 border-t border-gray-800 pt-3">
                  <p className="text-gray-300 text-sm whitespace-pre-wrap leading-relaxed">{m.message}</p>
                  <div className="flex items-center gap-2 mt-3">
                    <a
                      href={`mailto:${m.email}?subject=Re: ${encodeURIComponent(m.subject)}`}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition"
                    >
                      <Mail className="h-3 w-3" /> Reply via email
                    </a>
                    {!m.read && (
                      <button onClick={() => markRead(m.id)} disabled={!!actionId}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-300 text-xs font-medium transition disabled:opacity-40">
                        {actionId === m.id + 'read' ? <Loader2 className="h-3 w-3 animate-spin" /> : <MailOpen className="h-3 w-3" />} Mark read
                      </button>
                    )}
                    <button onClick={() => remove(m.id)} disabled={!!actionId}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-950 hover:bg-rose-900 text-rose-400 text-xs font-medium transition disabled:opacity-40 ml-auto">
                      {actionId === m.id + 'del' ? <Loader2 className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3 w-3" />} Delete
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {pages > 1 && (
        <div className="flex items-center justify-end gap-2">
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
