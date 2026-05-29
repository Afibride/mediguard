import React, { useEffect, useState, useCallback } from 'react';
import { Search, Shield, ShieldOff, UserX, UserCheck, Loader2, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react';
import { getAdminUsers, updateAdminUser, deleteAdminUser } from '@/services/adminApi';

function Badge({ children, color }) {
  const c = {
    green:  'bg-emerald-900/50 text-emerald-300 border-emerald-700',
    red:    'bg-rose-900/50 text-rose-300 border-rose-700',
    purple: 'bg-purple-900/50 text-purple-300 border-purple-700',
    gray:   'bg-gray-800 text-gray-400 border-gray-700',
  }[color] || 'bg-gray-800 text-gray-400 border-gray-700';
  return <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium border ${c}`}>{children}</span>;
}

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getAdminUsers(page, 20, search);
      setUsers(data.users);
      setTotal(data.total);
      setPages(data.pages);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => { load(); }, [load]);

  async function toggle(userId, field, currentValue) {
    setActionLoading(userId + field);
    try {
      await updateAdminUser(userId, { [field]: !currentValue });
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, [field]: !currentValue } : u));
    } catch (e) {
      alert(e.message);
    } finally {
      setActionLoading(null);
    }
  }

  async function remove(userId, email) {
    if (!confirm(`Delete user ${email}? This cannot be undone.`)) return;
    setActionLoading(userId + 'delete');
    try {
      await deleteAdminUser(userId);
      setUsers(prev => prev.filter(u => u.id !== userId));
      setTotal(t => t - 1);
    } catch (e) {
      alert(e.message);
    } finally {
      setActionLoading(null);
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-white">Users</h1>
          <p className="text-gray-400 text-sm">{total} registered accounts</p>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-500" />
          <input
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search email or name…"
            className="pl-8 pr-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-emerald-500 w-56"
          />
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-rose-400 bg-rose-950 border border-rose-800 rounded-lg p-3 text-sm">
          <AlertCircle className="h-4 w-4 flex-shrink-0" /> {error}
        </div>
      )}

      <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-48">
            <Loader2 className="h-6 w-6 text-emerald-400 animate-spin" />
          </div>
        ) : users.length === 0 ? (
          <div className="text-center text-gray-500 py-16 text-sm">No users found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800">
                  {['Name / Email', 'Status', 'Joined', 'Actions'].map(h => (
                    <th key={h} className="text-left text-xs text-gray-500 font-medium px-4 py-3">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {users.map(u => {
                  const busy = (k) => actionLoading === u.id + k;
                  return (
                    <tr key={u.id} className="hover:bg-gray-800/40 transition-colors">
                      <td className="px-4 py-3">
                        <p className="text-white font-medium">{u.full_name}</p>
                        <p className="text-gray-500 text-xs">{u.email}</p>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          <Badge color={u.is_active ? 'green' : 'red'}>{u.is_active ? 'Active' : 'Inactive'}</Badge>
                          {u.is_admin && <Badge color="purple">Admin</Badge>}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs">
                        {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => toggle(u.id, 'is_active', u.is_active)}
                            disabled={!!actionLoading}
                            title={u.is_active ? 'Deactivate' : 'Activate'}
                            className="p-1.5 rounded-lg hover:bg-gray-700 text-gray-400 hover:text-white transition disabled:opacity-40"
                          >
                            {busy('is_active') ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : u.is_active ? <UserX className="h-3.5 w-3.5" /> : <UserCheck className="h-3.5 w-3.5" />}
                          </button>
                          <button
                            onClick={() => toggle(u.id, 'is_admin', u.is_admin)}
                            disabled={!!actionLoading}
                            title={u.is_admin ? 'Remove admin' : 'Make admin'}
                            className="p-1.5 rounded-lg hover:bg-gray-700 text-gray-400 hover:text-yellow-400 transition disabled:opacity-40"
                          >
                            {busy('is_admin') ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : u.is_admin ? <ShieldOff className="h-3.5 w-3.5" /> : <Shield className="h-3.5 w-3.5" />}
                          </button>
                          <button
                            onClick={() => remove(u.id, u.email)}
                            disabled={!!actionLoading}
                            title="Delete user"
                            className="p-1.5 rounded-lg hover:bg-rose-950 text-gray-500 hover:text-rose-400 transition disabled:opacity-40 text-xs font-medium"
                          >
                            {busy('delete') ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : '✕'}
                          </button>
                        </div>
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
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500 text-xs">Page {page} of {pages}</span>
          <div className="flex gap-2">
            <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
              className="p-1.5 rounded-lg bg-gray-800 border border-gray-700 text-gray-300 hover:bg-gray-700 disabled:opacity-40">
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button disabled={page >= pages} onClick={() => setPage(p => p + 1)}
              className="p-1.5 rounded-lg bg-gray-800 border border-gray-700 text-gray-300 hover:bg-gray-700 disabled:opacity-40">
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
