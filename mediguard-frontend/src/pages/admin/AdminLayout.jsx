import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Users, Mail, TrendingUp,
  Stethoscope, MessageSquare, ThumbsUp, LogOut,
  Shield, Menu, X, ChevronRight,
} from 'lucide-react';
import { useAdminAuth } from '@/contexts/AdminAuthContext';

const NAV = [
  { to: '/admin/dashboard',  icon: LayoutDashboard, label: 'Dashboard'   },
  { to: '/admin/users',      icon: Users,            label: 'Users'       },
  { to: '/admin/newsletter', icon: Mail,             label: 'Newsletter'  },
  { to: '/admin/trends',     icon: TrendingUp,       label: 'Trends'      },
  { to: '/admin/diseases',   icon: Stethoscope,      label: 'Diseases'    },
  { to: '/admin/messages',   icon: MessageSquare,    label: 'Messages'    },
  { to: '/admin/feedback',   icon: ThumbsUp,         label: 'Feedback'    },
];

export default function AdminLayout() {
  const { admin, logoutAdmin } = useAdminAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  function handleLogout() {
    logoutAdmin();
    navigate('/admin', { replace: true });
  }

  const Sidebar = ({ mobile = false }) => (
    <aside className={`flex flex-col h-full bg-gray-900 border-r border-gray-800 ${mobile ? 'w-full' : 'w-56'}`}>
      {/* Brand */}
      <div className="flex items-center gap-2.5 px-4 py-5 border-b border-gray-800">
        <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center flex-shrink-0">
          <Shield className="h-4 w-4 text-white" />
        </div>
        <div className="min-w-0">
          <p className="text-white text-sm font-bold leading-none">MediGuard</p>
          <p className="text-emerald-400 text-[10px] font-medium mt-0.5">Admin Panel</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 space-y-0.5 overflow-y-auto">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            onClick={() => setSidebarOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 text-sm font-medium transition-colors rounded-lg mx-2 ${
                isActive
                  ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-600/30'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
              }`
            }
          >
            <Icon className="h-4 w-4 flex-shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Admin info + logout */}
      <div className="border-t border-gray-800 p-4">
        <div className="flex items-center gap-2.5 mb-3">
          <div className="w-7 h-7 rounded-full bg-emerald-700 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
            {(admin?.full_name || 'A')[0].toUpperCase()}
          </div>
          <div className="min-w-0">
            <p className="text-white text-xs font-medium truncate">{admin?.full_name || 'Admin'}</p>
            <p className="text-gray-500 text-[10px] truncate">{admin?.email}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-2 text-gray-400 hover:text-red-400 text-xs py-1.5 transition-colors"
        >
          <LogOut className="h-3.5 w-3.5" />
          Sign out
        </button>
      </div>
    </aside>
  );

  return (
    <div className="min-h-screen bg-gray-950 flex">
      {/* Desktop sidebar */}
      <div className="hidden md:flex flex-shrink-0 h-screen sticky top-0">
        <Sidebar />
      </div>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div className="w-64">
            <Sidebar mobile />
          </div>
          <div className="flex-1 bg-black/60" onClick={() => setSidebarOpen(false)} />
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        {/* Mobile topbar */}
        <div className="md:hidden flex items-center gap-3 px-4 py-3 bg-gray-900 border-b border-gray-800">
          <button onClick={() => setSidebarOpen(v => !v)} className="text-gray-400 hover:text-white">
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-emerald-400" />
            <span className="text-white text-sm font-semibold">MediGuard Admin</span>
          </div>
        </div>

        <main className="flex-1 p-4 sm:p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
