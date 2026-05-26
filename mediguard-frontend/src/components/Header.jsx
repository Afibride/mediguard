import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui/button';
import SettingsMenu from './SettingsMenu';
import MobileMenu from './MobileMenu';
import LocationBanner from './LocationBanner';
import { useAuth } from '@/components/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';

const LangToggle = () => {
  const { lang, switchLanguage } = useLanguage();
  const isEnglish = lang === 'en';
  
  return (
    <button
      onClick={() => switchLanguage(isEnglish ? 'fr' : 'en')}
      className="flex h-8 w-16 items-center justify-center rounded-full border border-border bg-background text-sm font-medium transition-all hover:bg-muted hover:scale-105"
      aria-label={isEnglish ? 'Switch to French' : 'Passer à l\'anglais'}
    >
      <span className={`transition-all duration-200 ${isEnglish ? 'text-primary font-bold' : 'text-muted-foreground'}`}>
        EN
      </span>
      <span className="mx-1 text-muted-foreground">|</span>
      <span className={`transition-all duration-200 ${!isEnglish ? 'text-primary font-bold' : 'text-muted-foreground'}`}>
        FR
      </span>
    </button>
  );
};

const Header = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isDesktop, setIsDesktop] = useState(window.innerWidth > 768);
  const [isDark, setIsDark] = useState(false);
  const [showLocBanner, setShowLocBanner] = useState(false);
  const location = useLocation();
  const { user } = useAuth();
  const { t } = useLanguage();

  useEffect(() => {
    if (document.documentElement.classList.contains('dark')) setIsDark(true);
  }, []);

  useEffect(() => {
    // Show location banner after a short delay, only if not yet dismissed/granted
    const timer = setTimeout(() => {
      const dismissed = localStorage.getItem('mg_loc_dismissed') === '1';
      if (!dismissed && navigator.geolocation) {
        navigator.permissions?.query({ name: 'geolocation' }).then(r => {
          if (r.state === 'prompt') setShowLocBanner(true);
        }).catch(() => setShowLocBanner(true));
      }
    }, 2500);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    const handleResize = () => {
      setIsDesktop(window.innerWidth > 768);
      if (window.innerWidth > 768) setIsMobileMenuOpen(false);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    document.body.style.overflow = isMobileMenuOpen ? 'hidden' : 'unset';
    return () => { document.body.style.overflow = 'unset'; };
  }, [isMobileMenuOpen]);

  const toggleTheme = () => {
    if (isDark) {
      document.documentElement.classList.remove('dark');
      setIsDark(false);
    } else {
      document.documentElement.classList.add('dark');
      setIsDark(true);
    }
  };

  const navLinks = [
    { key: 'nav_home',           path: '/' },
    { key: 'nav_symptom_checker', path: '/symptom-checker' },
    { key: 'nav_disease_library', path: '/disease-library' },
    { key: 'nav_chat_ai',         path: '/chat-ai' },
    { key: 'nav_facilities',      path: '/nearby-facilities' },
    { key: 'nav_trends',          path: '/trends' },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/82 transition-all duration-300">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center space-x-2 hover:opacity-80 transition-opacity">
          <img src="/mediguard.png" alt="MediGuard Logo" className="logo-xs" />
        </Link>

        {isDesktop ? (
          <>
            {/* Desktop nav */}
            <nav className="flex items-center justify-center space-x-4">
              {navLinks.map((link) => (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`text-sm font-medium transition-all duration-200 relative group ${
                    isActive(link.path) ? 'text-primary' : 'text-gray-600 dark:text-gray-300 hover:text-primary'
                  }`}
                >
                  {t(link.key)}
                  <span className={`absolute -bottom-1 left-0 w-full h-0.5 bg-primary transition-transform origin-left duration-300 ${
                    isActive(link.path) ? 'scale-x-100' : 'scale-x-0 group-hover:scale-x-100'
                  }`} />
                </Link>
              ))}
            </nav>

            {/* Right controls */}
            <div className="flex items-center space-x-2">
              <LangToggle />
              {user ? (
                <SettingsMenu />
              ) : (
                <>
                  <Button variant="ghost" size="icon" onClick={toggleTheme}
                    className="min-h-[40px] min-w-[40px] rounded-full hover:bg-gray-100 dark:hover:bg-gray-800"
                    aria-label="Toggle theme">
                    {isDark ? <Sun className="h-5 w-5 text-gray-600 dark:text-gray-300" /> : <Moon className="h-5 w-5 text-gray-600 dark:text-gray-300" />}
                  </Button>
                  <Link to="/login">
                    <Button variant="ghost" size="sm" className="font-medium hover:text-primary">{t('nav_login')}</Button>
                  </Link>
                  <Link to="/signup">
                    <Button size="sm" className="font-medium bg-primary hover:bg-primary/90 text-white">{t('nav_register')}</Button>
                  </Link>
                </>
              )}
            </div>
          </>
        ) : (
          /* Mobile: language toggle + hamburger */
          <div className="flex items-center gap-2">
            <LangToggle />
            <Button variant="ghost" size="icon" onClick={() => setIsMobileMenuOpen(true)}
              className="min-h-[44px] min-w-[44px] hover:bg-gray-100 dark:hover:bg-gray-800" aria-label="Open Menu">
              <Menu className="h-6 w-6 text-gray-900 dark:text-gray-100" />
            </Button>
          </div>
        )}
      </div>

      {/* Location permission banner — shown once, below header */}
      {showLocBanner && (
        <LocationBanner onGranted={() => setShowLocBanner(false)} />
      )}

      <MobileMenu isOpen={isMobileMenuOpen} onClose={() => setIsMobileMenuOpen(false)} isLoggedIn={!!user} />
    </header>
  );
};

export default Header;
