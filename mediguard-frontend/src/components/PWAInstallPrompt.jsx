/**
 * PWAInstallPrompt.jsx
 *
 * Shows platform-appropriate install instructions:
 *  • iOS Safari  — "Tap Share → Add to Home Screen"
 *  • Android/Chrome — uses native beforeinstallprompt event
 *
 * Dismisses per-session (sessionStorage). Won't show if already installed.
 */
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Share, Download } from 'lucide-react';

// Detect iOS (iPhone/iPad/iPod) in Safari
function detectPlatform() {
  const ua = navigator.userAgent || '';
  const isIOS = /iphone|ipad|ipod/i.test(ua);
  const isSafari = /safari/i.test(ua) && !/chrome|chromium|crios|fxios/i.test(ua);
  const isAndroid = /android/i.test(ua);
  const isChrome = /chrome|chromium/i.test(ua) && !/edge|opr\//i.test(ua);
  // Already installed — display-mode standalone
  const isStandalone =
    window.matchMedia('(display-mode: standalone)').matches ||
    window.navigator.standalone === true;

  return { isIOS, isSafari, isAndroid, isChrome, isStandalone };
}

export default function PWAInstallPrompt() {
  const [show, setShow] = useState(false);
  const [platform, setPlatform] = useState(null);
  const [deferredPrompt, setDeferredPrompt] = useState(null);

  useEffect(() => {
    // Don't show if already dismissed this session
    if (sessionStorage.getItem('mg_pwa_dismissed') === '1') return;

    const p = detectPlatform();
    if (p.isStandalone) return; // already installed

    // Android/Chrome — wait for beforeinstallprompt
    const handleInstallable = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setPlatform('android');
      setShow(true);
    };
    window.addEventListener('beforeinstallprompt', handleInstallable);

    // iOS Safari — show manual instructions
    if (p.isIOS && p.isSafari) {
      // Small delay so it doesn't flash on first render
      const timer = setTimeout(() => {
        setPlatform('ios');
        setShow(true);
      }, 3000);
      return () => {
        clearTimeout(timer);
        window.removeEventListener('beforeinstallprompt', handleInstallable);
      };
    }

    return () => window.removeEventListener('beforeinstallprompt', handleInstallable);
  }, []);

  const dismiss = () => {
    sessionStorage.setItem('mg_pwa_dismissed', '1');
    setShow(false);
  };

  const handleAndroidInstall = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      sessionStorage.setItem('mg_pwa_dismissed', '1');
    }
    setShow(false);
    setDeferredPrompt(null);
  };

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ y: 80, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 80, opacity: 0 }}
          transition={{ type: 'spring', damping: 22, stiffness: 200 }}
          className="fixed bottom-4 left-3 right-3 z-50 mx-auto max-w-sm"
        >
          <div className="rounded-2xl border border-primary/20 bg-background/98 shadow-xl backdrop-blur-sm px-4 py-3.5 flex gap-3 items-start">
            {/* App icon */}
            <img
              src="/mediguard.png"
              alt="MediGuard"
              className="h-11 w-11 rounded-xl flex-shrink-0 shadow-sm"
            />

            <div className="flex-1 min-w-0">
              <p className="text-sm font-bold text-foreground leading-tight">
                Install MediGuard
              </p>

              {platform === 'ios' ? (
                <p className="text-xs text-muted-foreground mt-1 leading-snug">
                  Tap the{' '}
                  <span className="inline-flex items-center gap-0.5 font-semibold text-primary">
                    <Share className="h-3 w-3" /> Share
                  </span>{' '}
                  button below, then tap{' '}
                  <span className="font-semibold text-primary">Add to Home Screen</span>
                </p>
              ) : (
                <p className="text-xs text-muted-foreground mt-1 leading-snug">
                  Install for fast access, offline use &amp; no browser bar
                </p>
              )}

              {platform === 'android' && (
                <button
                  onClick={handleAndroidInstall}
                  className="mt-2 flex items-center gap-1.5 rounded-full bg-primary px-3 py-1.5 text-xs font-semibold text-white hover:bg-primary/90 transition-colors"
                >
                  <Download className="h-3 w-3" /> Install App
                </button>
              )}

              {platform === 'ios' && (
                <div className="mt-2 flex items-center gap-1 text-[10px] text-muted-foreground">
                  <span>Works offline · No app store needed · Free</span>
                </div>
              )}
            </div>

            <button
              onClick={dismiss}
              className="flex-shrink-0 p-1 rounded-full text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              title="Dismiss"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
