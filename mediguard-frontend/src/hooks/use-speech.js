import { useCallback, useEffect, useRef, useState } from 'react';

const supported = typeof window !== 'undefined' && 'speechSynthesis' in window;

// Preferred language codes in order — African English first, then British as fallback.
const AFRICAN_LANGS = ['en-NG', 'en-ZA', 'en-GH', 'en-KE', 'en-TZ', 'en-UG', 'en-CM'];

/**
 * Pick the best available voice, preferring African English variants.
 * Falls back to en-GB, then any English voice, then the browser default.
 */
function pickAfricanVoice() {
  if (!supported) return null;
  const voices = window.speechSynthesis.getVoices();
  if (!voices.length) return null;

  // 1. Exact African English match
  for (const lang of AFRICAN_LANGS) {
    const v = voices.find(v => v.lang === lang);
    if (v) return v;
  }
  // 2. Any voice whose lang starts with an African English code
  for (const lang of AFRICAN_LANGS) {
    const v = voices.find(v => v.lang.startsWith(lang.split('-')[0] + '-'));
    if (v && v.lang !== 'en-US') return v;
  }
  // 3. British English — closer to West-African cadence than US
  const gb = voices.find(v => v.lang === 'en-GB');
  if (gb) return gb;
  // 4. Any non-US English
  const anyEn = voices.find(v => v.lang.startsWith('en-') && v.lang !== 'en-US');
  if (anyEn) return anyEn;
  // 5. Any English
  return voices.find(v => v.lang.startsWith('en')) || null;
}

export function useSpeech() {
  const [speaking, setSpeaking] = useState(false);
  const utteranceRef = useRef(null);
  // Cache voices once loaded — they load asynchronously in most browsers
  const voicesRef = useRef(null);

  useEffect(() => {
    if (!supported) return;
    const load = () => { voicesRef.current = window.speechSynthesis.getVoices(); };
    load();
    window.speechSynthesis.onvoiceschanged = load;
    return () => {
      window.speechSynthesis.cancel();
      window.speechSynthesis.onvoiceschanged = null;
    };
  }, []);

  const speak = useCallback((text) => {
    if (!supported || !text) return;
    window.speechSynthesis.cancel();

    const utt = new SpeechSynthesisUtterance(text);

    // Apply best available African voice
    const voice = pickAfricanVoice();
    if (voice) {
      utt.voice = voice;
      utt.lang  = voice.lang;
    } else {
      utt.lang = 'en-NG';  // hint to the browser even without a matched voice
    }

    // Smooth, deliberate pacing — warm and unhurried
    utt.rate  = 0.88;
    utt.pitch = 0.95;

    utt.onstart = () => setSpeaking(true);
    utt.onend   = () => setSpeaking(false);
    utt.onerror = () => setSpeaking(false);

    utteranceRef.current = utt;
    window.speechSynthesis.speak(utt);
  }, []);

  const stop = useCallback(() => {
    if (supported) window.speechSynthesis.cancel();
    setSpeaking(false);
  }, []);

  return { speak, stop, speaking, supported };
}
