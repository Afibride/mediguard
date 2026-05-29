import React, { useEffect, useState, useCallback } from 'react';
import { Search, Star, StarOff, Loader2, ChevronLeft, ChevronRight } from 'lucide-react';
import { getAdminDiseases, updateAdminDisease } from '@/services/adminApi';

const SEVERITY_COLORS = { High: 'text-rose-400 bg-rose-900/40 border-rose-700', Medium: 'text-amber-400 bg-amber-900/40 border-amber-700', Low: 'text-emerald-400 bg-emerald-900/40 border-emerald-700' };

export default function AdminDiseases() {
  const [diseases, setDiseases] = useState([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [actionSlug, setActionSlug] = useState(null);
  const [editSlug, setEditSlug] = useState(null);
  const [editSeverity, setEditSeverity] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getAdminDiseases(page, 20, search);
      setDiseases(data.diseases);
      setTotal(data.total);
      setPages(data.pages);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [page, search]);

  useEffect(() => { load(); }, [load]);

  async function toggleFeatured(slug, featured) {
    setActionSlug(slug + 'feat');
    try {
      await updateAdminDisease(slug, { featured: !featured });
      setDiseases(prev => prev.map(d => d.slug === slug ? { ...d, featured: !featured } : d));
    } catch (e) { alert(e.message); }
    finally { setActionSlug(null); }
  }

  async function saveSeverity(slug) {
    setActionSlug(slug + 'sev');
    try {
      await updateAdminDisease(slug, { severity: editSeverity });
      setDiseases(prev => prev.map(d => d.slug === slug ? { ...d, severity: editSeverity } : d));
      setEditSlug(null);
    } catch (e) { alert(e.message); }
    finally { setActionSlug(null); }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-white">Diseases</h1>
          <p className="text-gray-400 text-sm">{total} diseases in library</p>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-500" />
          <input value={search} onChange={e => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search diseases…"
            className="pl-8 pr-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-emerald-500 w-52" />
        </div>
      </div>

      <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-48"><Loader2 className="h-6 w-6 text-emerald-400 animate-spin" /></div>
        ) : diseases.length === 0 ? (
          <div className="text-center text-gray-500 py-16 text-sm">No diseases found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800">
                  {['Disease', 'Category', 'Severity', 'Symptoms', 'Featured', 'Actions'].map(h => (
                    <th key={h} className="text-left text-xs text-gray-500 font-medium px-4 py-3">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {diseases.map(d => {
                  const sev = SEVERITY_COLORS[d.severity] || SEVERITY_COLORS.Medium;
                  return (
                    <tr key={d.slug} className="hover:bg-gray-800/40 transition-colors">
                      <td className="px-4 py-3">
                        <p className="text-white font-medium">{d.name}</p>
                        <p className="text-gray-500 text-[10px] mt-0.5 line-clamp-1">{d.description}</p>
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs">{d.category}</td>
                      <td className="px-4 py-3">
                        {editSlug === d.slug ? (
                          <div className="flex items-center gap-1">
                            <select value={editSeverity} onChange={e => setEditSeverity(e.target.value)}
                              className="rounded bg-gray-800 border border-gray-600 text-white text-xs px-1.5 py-1 focus:outline-none focus:border-emerald-500">
                              {['Low','Medium','High'].map(s => <option key={s}>{s}</option>)}
                            </select>
                            <button onClick={() => saveSeverity(d.slug)} disabled={!!actionSlug}
                              className="px-2 py-1 rounded bg-emerald-600 text-white text-[10px] font-medium hover:bg-emerald-500 disabled:opacity-40">
                              {actionSlug === d.slug + 'sev' ? '…' : 'Save'}
                            </button>
                            <button onClick={() => setEditSlug(null)} className="px-2 py-1 rounded bg-gray-700 text-gray-300 text-[10px]">✕</button>
                          </div>
                        ) : (
                          <button onClick={() => { setEditSlug(d.slug); setEditSeverity(d.severity); }}
                            className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium border cursor-pointer hover:opacity-80 transition ${sev}`}>
                            {d.severity}
                          </button>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs">{d.symptom_count}</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs ${d.featured ? 'text-yellow-400' : 'text-gray-600'}`}>
                          {d.featured ? '★ Featured' : '—'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => toggleFeatured(d.slug, d.featured)}
                          disabled={!!actionSlug}
                          title={d.featured ? 'Remove from featured' : 'Mark as featured'}
                          className="p-1.5 rounded hover:bg-gray-700 text-gray-400 hover:text-yellow-400 transition disabled:opacity-40"
                        >
                          {actionSlug === d.slug + 'feat' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : d.featured ? <StarOff className="h-3.5 w-3.5" /> : <Star className="h-3.5 w-3.5" />}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

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
