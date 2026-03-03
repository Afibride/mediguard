
import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { MoreVertical, Moon, Sun, History, LogOut } from 'lucide-react';
import { useAuth } from '@/components/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';

const SettingsMenu = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isDark, setIsDark] = useState(false);
  const menuRef = useRef(null);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (document.documentElement.classList.contains('dark')) {
      setIsDark(true);
    }
  }, []);

  if (!user) return null;

  const toggleTheme = () => {
    if (isDark) {
      document.documentElement.classList.remove('dark');
      setIsDark(false);
    } else {
      document.documentElement.classList.add('dark');
      setIsDark(true);
    }
  };

  const handleLogout = () => {
    logout();
    setIsOpen(false);
    navigate('/');
  };

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 rounded-full hover:bg-muted/80 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50"
        aria-label="Settings Menu"
      >
        <MoreVertical className="w-5 h-5 text-foreground" />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 mt-2 w-48 bg-card border shadow-xl rounded-lg overflow-hidden z-50 origin-top-right"
          >
            <div className="py-1">
              <button
                onClick={toggleTheme}
                className="w-full text-left px-4 py-2 text-sm text-foreground hover:bg-primary/10 hover:text-primary transition-colors flex items-center gap-2"
              >
                {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                {isDark ? 'Light Mode' : 'Dark Mode'}
              </button>

              <Link
                to="/history"
                onClick={() => setIsOpen(false)}
                className="w-full text-left px-4 py-2 text-sm text-foreground hover:bg-primary/10 hover:text-primary transition-colors flex items-center gap-2"
              >
                <History className="w-4 h-4" />
                History
              </Link>
              
              <div className="border-t my-1"></div>
              
              <button
                onClick={handleLogout}
                className="w-full text-left px-4 py-2 text-sm text-destructive hover:bg-destructive/10 transition-colors flex items-center gap-2"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SettingsMenu;
