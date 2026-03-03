import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Moon, Sun, History, LogOut, Home, Activity, BookOpen, Bot, TrendingUp, LogIn, UserPlus } from 'lucide-react';
import { useAuth } from '@/components/AuthContext';

const MobileMenu = ({ isOpen, onClose, isLoggedIn }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [isDark, setIsDark] = useState(false);

  // Initialize theme
  useEffect(() => {
    if (document.documentElement.classList.contains('dark')) {
      setIsDark(true);
    }
  }, []);

  // Theme toggle logic updates document element class list
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
    onClose();
    navigate('/');
  };

  const baseNavLinks = [
    { name: 'Home', path: '/', icon: Home },
    { name: 'Symptom Checker', path: '/symptom-checker', icon: Activity },
    { name: 'Disease Library', path: '/disease-library', icon: BookOpen },
    { name: 'MediGuard AI', path: '/chat-ai', icon: Bot },
    { name: 'Trends Dashboard', path: '/trends', icon: TrendingUp },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Dark Overlay Background - lower z-index than menu */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-100"
            onClick={onClose}
          />
          
          {/* Slide-in Menu Panel - positioned on top of header with higher z-index */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 250 }}
            className="fixed top-0 right-0 bottom-0 w-[280px] bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-800 shadow-2xl z-[60] flex flex-col"
          >
            {/* Header / Close Button */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
              <img 
                src="/mediguard.png" 
                alt="MediGuard Logo" 
                className="logo-sm"
              />
              <button 
                onClick={onClose}
                className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors focus:outline-none"
                aria-label="Close Menu"
              >
                <X className="w-6 h-6 text-gray-900 dark:text-gray-100" />
              </button>
            </div>

            {/* Navigation Links - stretched to fill available space */}
            <div className="flex-1 flex flex-col bg-white dark:bg-gray-900">
              {/* Main Navigation */}
              <div className="py-6 px-3">
                <div className="space-y-1">
                  {baseNavLinks.map((link) => (
                    <Link
                      key={link.path}
                      to={link.path}
                      onClick={onClose}
                      className={`flex items-center gap-3 px-4 py-3 rounded-lg text-base font-medium transition-colors last:mb-4 ${
                        isActive(link.path)
                          ? 'bg-primary/10 text-primary'
                          : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800'
                      }`}
                    >
                      <link.icon className={`w-5 h-5 ${
                        isActive(link.path) 
                          ? 'text-primary' 
                          : 'text-gray-500 dark:text-gray-400'
                      }`} />
                      {link.name}
                    </Link>
                  ))}
                </div>
              </div>

              {/* Bottom Section */}
              <div className="mt-auto border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
                <div className="p-3 space-y-2 pb-6">
                  {/* Conditional Auth & Theme Links */}
                  {isLoggedIn ? (
                    <>
                      <Link
                        to="/history"
                        onClick={onClose}
                        className={`flex items-center gap-3 px-4 py-3 rounded-lg text-base font-medium transition-colors last:mb-4 ${
                          isActive('/history')
                            ? 'bg-primary/10 text-primary'
                            : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800'
                        }`}
                      >
                        <History className={`w-5 h-5 ${
                          isActive('/history') 
                            ? 'text-primary' 
                            : 'text-gray-500 dark:text-gray-400'
                        }`} />
                        History
                      </Link>
                      
                      <button
                        onClick={toggleTheme}
                        className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-base font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-left last:mb-4"
                      >
                        {isDark ? (
                          <Sun className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                        ) : (
                          <Moon className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                        )}
                        {isDark ? 'Light Mode' : 'Dark Mode'}
                      </button>
                      
                      <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-base font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors text-left last:mb-4"
                      >
                        <LogOut className="w-5 h-5" />
                        Logout
                      </button>
                    </>
                  ) : (
                    <>
                      <Link
                        to="/login"
                        onClick={onClose}
                        className="flex items-center gap-3 px-4 py-3 rounded-lg text-base font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors last:mb-4"
                      >
                        <LogIn className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                        Login
                      </Link>
                      
                      <Link
                        to="/signup"
                        onClick={onClose}
                        className="flex items-center gap-3 px-4 py-3 rounded-lg text-base font-medium bg-primary/10 text-primary hover:bg-primary hover:text-white transition-colors last:mb-4"
                      >
                        <UserPlus className="w-5 h-5" />
                        Register
                      </Link>
                      
                      <div className="my-2 border-t border-gray-200 dark:border-gray-800"></div>
                      
                      <button
                        onClick={toggleTheme}
                        className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-base font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-left last:mb-4"
                      >
                        {isDark ? (
                          <Sun className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                        ) : (
                          <Moon className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                        )}
                        {isDark ? 'Light Mode' : 'Dark Mode'}
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default MobileMenu;