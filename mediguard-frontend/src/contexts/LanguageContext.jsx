import React, { createContext, useContext, useState, useCallback } from 'react';
import translations from '@/i18n/translations';

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(() => {
    try {
      return localStorage.getItem('mg_lang') || 'en';
    } catch {
      return 'en';
    }
  });

  const switchLanguage = useCallback((code) => {
    setLang(code);
    try { localStorage.setItem('mg_lang', code); } catch {}
  }, []);

  const t = useCallback((key) => {
    return translations[lang]?.[key] ?? translations['en']?.[key] ?? key;
  }, [lang]);

  return (
    <LanguageContext.Provider value={{ lang, switchLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useLanguage must be used inside LanguageProvider');
  return ctx;
}
