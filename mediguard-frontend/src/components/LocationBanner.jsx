import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MapPin, X, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/contexts/LanguageContext';

export function useUserLocation() {
  const [location, setLocation] = useState(null);
  const [status, setStatus] = useState('idle'); // idle | granted | denied | unsupported

  useEffect(() => {
    // Check if already granted without prompting
    if (navigator.permissions) {
      navigator.permissions.query({ name: 'geolocation' }).then((result) => {
        if (result.state === 'granted') {
          requestLocation();
        } else if (result.state === 'denied') {
          setStatus('denied');
        }
        // 'prompt' → wait for user action
      }).catch(() => {});
    }
  }, []);

  const requestLocation = () => {
    if (!navigator.geolocation) {
      setStatus('unsupported');
      return;
    }
    setStatus('requesting');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setStatus('granted');
      },
      () => setStatus('denied'),
      { timeout: 10000, maximumAge: 300000 }
    );
  };

  return { location, status, requestLocation };
}

const LocationBanner = ({ onGranted }) => {
  const { t } = useLanguage();
  const { location, status, requestLocation } = useUserLocation();
  const [dismissed, setDismissed] = useState(() => {
    try { return localStorage.getItem('mg_loc_dismissed') === '1'; } catch { return false; }
  });

  useEffect(() => {
    if (status === 'granted' && location && onGranted) {
      onGranted(location);
    }
  }, [status, location]);

  const dismiss = () => {
    setDismissed(true);
    try { localStorage.setItem('mg_loc_dismissed', '1'); } catch {}
  };

  if (dismissed || status === 'denied' || status === 'granted') {
    return status === 'granted' ? (
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0 }}
        className="mx-4 mt-3 flex items-center gap-2 rounded-lg bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 px-4 py-2.5 text-sm text-green-700 dark:text-green-400"
      >
        <CheckCircle2 className="h-4 w-4 shrink-0" />
        <span>{t('loc_granted')}</span>
      </motion.div>
    ) : null;
  }

  if (status === 'requesting' || status === 'idle') {
    return (
      <AnimatePresence>
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          className="mx-4 mt-3 flex items-start gap-3 rounded-xl border border-primary/30 bg-primary/5 px-4 py-3"
        >
          <MapPin className="h-5 w-5 text-primary mt-0.5 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-sm text-foreground">{t('loc_banner_title')}</p>
            <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">{t('loc_banner_body')}</p>
            <div className="flex gap-2 mt-2.5 flex-wrap">
              <Button
                size="sm"
                onClick={requestLocation}
                disabled={status === 'requesting'}
                className="gap-1.5 h-8 text-xs"
              >
                <MapPin className="h-3.5 w-3.5" />
                {status === 'requesting' ? t('fac_locating') : t('loc_allow')}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={dismiss}
                className="h-8 text-xs text-muted-foreground"
              >
                {t('loc_dismiss')}
              </Button>
            </div>
          </div>
          <button onClick={dismiss} className="p-1 rounded hover:bg-muted text-muted-foreground shrink-0">
            <X className="h-4 w-4" />
          </button>
        </motion.div>
      </AnimatePresence>
    );
  }

  return null;
};

export default LocationBanner;
