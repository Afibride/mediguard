import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Moon, Sun, History, LogOut, Home, Activity, BookOpen, Bot, TrendingUp, LogIn, UserPlus, User, MapPin } from 'lucide-react';
import { useAuth } from '@/components/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';

const MobileMenu = ({ isOpen, onClose, isLoggedIn }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const { lang, switchLanguage, t } = useLanguage();
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
    { key: 'nav_home',            path: '/',                  icon: Home },
    { key: 'nav_symptom_checker', path: '/symptom-checker',   icon: Activity },
    { key: 'nav_disease_library', path: '/disease-library',   icon: BookOpen },
    { key: 'nav_chat_ai',         path: '/chat-ai',           icon: Bot },
    { key: 'nav_facilities',      path: '/nearby-facilities', icon: MapPin },
    { key: 'nav_trends',          path: '/trends',            icon: TrendingUp },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Dark Overlay — covers full viewport, click anywhere outside menu to close */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[55]"
            onClick={onClose}
            aria-hidden="true"
          />

          {/* Slide-in Menu Panel */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 250 }}
            className="fixed top-0 right-0 bottom-0 w-[280px] bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-800 shadow-2xl z-[60] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header: Logo + Theme toggle + Close button */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
              {/* Logo + theme icon side-by-side */}
              <div className="flex items-center gap-2">
                <img
                  src="/mediguard.png"
                  alt="MediGuard Logo"
                  className="logo-sm"
                />
                <button
                  onClick={toggleTheme}
                  className="min-h-[36px] min-w-[36px] flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors focus:outline-none"
                  aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
                >
                  {isDark
                    ? <Sun  className="w-5 h-5 text-amber-400" />
                    : <Moon className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                  }
                </button>
              </div>

              {/* Close button */}
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
                      {t(link.key)}
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
                        to="/profile"
                        onClick={onClose}
                        className={`flex items-center gap-3 px-4 py-3 rounded-lg text-base font-medium transition-colors last:mb-4 ${
                          isActive('/profile')
                            ? 'bg-primary/10 text-primary'
                            : 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800'
                        }`}
                      >
                        <User className={`w-5 h-5 ${
                          isActive('/profile') 
                            ? 'text-primary' 
                            : 'text-gray-500 dark:text-gray-400'
                        }`} />
                        Profile
                      </Link>

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
                        {t('nav_history')}
                      </Link>

                      <button
                        onClick={() => switchLanguage(lang === 'en' ? 'fr' : 'en')}
                        className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-base font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-left"
                      >
                        <span className="text-lg w-5 text-center">{lang === 'en' ? '🇫🇷' : '🇬🇧'}</span>
                        {lang === 'en' ? 'Français' : 'English'}
                      </button>

                      <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-base font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors text-left last:mb-4"
                      >
                        <LogOut className="w-5 h-5" />
                        {t('nav_logout')}
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
                        {t('nav_login')}
                      </Link>

                      <Link
                        to="/signup"
                        onClick={onClose}
                        className="flex items-center gap-3 px-4 py-3 rounded-lg text-base font-medium bg-primary/10 text-primary hover:bg-primary hover:text-white transition-colors last:mb-4"
                      >
                        <UserPlus className="w-5 h-5" />
                        {t('nav_register')}
                      </Link>

                      <div className="my-2 border-t border-gray-200 dark:border-gray-800" />

                      <button
                        onClick={() => switchLanguage(lang === 'en' ? 'fr' : 'en')}
                        className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-base font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-left"
                      >
                        <span className="text-lg w-5 text-center">{lang === 'en' ? '🇫🇷' : '🇬🇧'}</span>
                        {lang === 'en' ? 'Français' : 'English'}
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
