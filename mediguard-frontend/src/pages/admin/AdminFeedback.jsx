import React, { useEffect, useState, useCallback } from 'react';
import { ThumbsUp, ThumbsDown, Loader2, ChevronLeft, ChevronRight } from 'lucide-react';
import { getAdminFeedback } from '@/services/adminApi';

export default function AdminFeedback() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState(null); // null=all, true=helpful, false=not helpful
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getAdminFeedback(page, filter);
      setItems(data.feedback);
      setTotal(data.total);
      setPages(data.pages);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [page, filter]);

  useEffect(() => { load(); }, [load]);

  const filterBtns = [
    { label: 'All', value: null },
    { label: 'Helpful', value: true },
    { label: 'Not helpful', value: false },
  ];

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-white">Chat Feedback</h1>
          <p className="text-gray-400 text-sm">{total} ratings collected</p>
        </div>
        <div className="flex gap-1.5">
          {filterBtns.map(({ label, value }) => (
            <button key={label} onClick={() => { setFilter(value); setPage(1); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${filter === value ? 'bg-emerald-600 border-emerald-600 text-white' : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-emerald-500 hover:text-white'}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48"><Loader2 className="h-6 w-6 text-emerald-400 animate-spin" /></div>
      ) : items.length === 0 ? (
        <div className="bg-gray-900 rounded-xl border border-gray-800 py-16 text-center text-gray-500 text-sm">No feedback found</div>
      ) : (
        <div className="space-y-2">
          {items.map(f => (
            <div key={f.id} className={`bg-gray-900 rounded-xl border p-4 ${f.helpful ? 'border-emerald-800/50' : 'border-rose-900/50'}`}>
              <div className="flex items-start gap-3">
                <div className={`flex-shrink-0 mt-0.5 ${f.helpful ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {f.helpful ? <ThumbsUp className="h-4 w-4" /> : <ThumbsDown className="h-4 w-4" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    {f.mode && <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-gray-800 text-gray-400 border border-gray-700">{f.mode}</span>}
                    <span className="text-gray-600 text-[10px]">{f.created_at ? new Date(f.created_at).toLocaleDateString() : ''}</span>
                  </div>
                  <p className="text-gray-200 text-sm font-medium leading-snug">{f.query}</p>
                  {f.response_preview && (
                    <p className="text-gray-500 text-xs mt-1.5 line-clamp-2 leading-relaxed border-l-2 border-gray-700 pl-2">{f.response_preview}</p>
                  )}
                </div>
              </div>
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
