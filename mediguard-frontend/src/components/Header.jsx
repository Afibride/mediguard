import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui/button';
import SettingsMenu from './SettingsMenu';
import MobileMenu from './MobileMenu';
import { useAuth } from '@/components/AuthContext';

const Header = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isDesktop, setIsDesktop] = useState(window.innerWidth > 768);
  const [isDark, setIsDark] = useState(false);
  const location = useLocation();
  const { user } = useAuth();

  // Initialize theme
  useEffect(() => {
    if (document.documentElement.classList.contains('dark')) {
      setIsDark(true);
    }
  }, []);

  // Responsive breakpoint logic
  useEffect(() => {
    const handleResize = () => {
      const desktopView = window.innerWidth > 768;
      setIsDesktop(desktopView);
      if (desktopView) {
        setIsMobileMenuOpen(false);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isMobileMenuOpen]);

  // Theme toggle logic
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
    { name: 'Home', path: '/' },
    { name: 'Symptom Checker', path: '/symptom-checker' },
    { name: 'Disease Library', path: '/disease-library' },
    { name: 'Chat AI', path: '/chat-ai' },
    { name: 'Trends Dashboard', path: '/trends' },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-white/95 dark:bg-gray-900/95 backdrop-blur supports-[backdrop-filter]:bg-white/60 dark:supports-[backdrop-filter]:bg-gray-900/60 transition-all duration-300">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        
        {/* Left: Logo */}
        <Link to="/" className="flex items-center space-x-2 hover:opacity-80 transition-opacity">
          <img 
            src="/public/mediguard.png" 
            alt="MediGuard Logo" 
            className="logo-xs"
          />
        </Link>

        {isDesktop ? (
          <>
            {/* Center: Desktop Navigation Links */}
            <nav className="flex items-center justify-center space-x-6">
              {navLinks.map((link) => (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`text-sm font-medium transition-all duration-200 relative group ${
                    isActive(link.path) 
                      ? 'text-primary' 
                      : 'text-gray-600 dark:text-gray-300 hover:text-primary'
                  }`}
                >
                  {link.name}
                  <span className={`absolute -bottom-1 left-0 w-full h-0.5 bg-primary transition-transform origin-left duration-300 ${
                    isActive(link.path) ? 'scale-x-100' : 'scale-x-0 group-hover:scale-x-100'
                  }`}></span>
                </Link>
              ))}
            </nav>

            {/* Right: Settings Menu or Auth Buttons with Theme Toggle */}
            <div className="flex items-center space-x-4">
              {user ? (
                <SettingsMenu />
              ) : (
                <div className="flex items-center space-x-2">
                  {/* Theme Toggle Button for non-logged-in users */}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={toggleTheme}
                    className="min-h-[40px] min-w-[40px] rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                    aria-label="Toggle theme"
                  >
                    {isDark ? (
                      <Sun className="h-5 w-5 text-gray-600 dark:text-gray-300" />
                    ) : (
                      <Moon className="h-5 w-5 text-gray-600 dark:text-gray-300" />
                    )}
                  </Button>
                  
                  <Link to="/login">
                    <Button variant="ghost" size="sm" className="font-medium hover:text-primary transition-colors">
                      Login
                    </Button>
                  </Link>
                  <Link to="/signup">
                    <Button size="sm" className="font-medium bg-primary hover:bg-primary/90 text-white transition-colors">
                      Register
                    </Button>
                  </Link>
                </div>
              )}
            </div>
          </>
        ) : (
          /* Mobile View: Hamburger Menu Icon */
          <div className="flex items-center">
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={() => setIsMobileMenuOpen(true)}
              className="min-h-[44px] min-w-[44px] hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label="Open Menu"
            >
              <Menu className="h-6 w-6 text-gray-900 dark:text-gray-100" />
            </Button>
          </div>
        )}
      </div>

      {/* Mobile Slide-in Menu */}
      <MobileMenu 
        isOpen={isMobileMenuOpen} 
        onClose={() => setIsMobileMenuOpen(false)} 
        isLoggedIn={!!user} 
      />
    </header>
  );
};

export default Header;