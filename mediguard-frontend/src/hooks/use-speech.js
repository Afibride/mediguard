/**
 * use-speech.js — MediGuard text-to-speech hook
 *
 * Voice selection priority (smooth West/Central-African cadence):
 *   en-NG (Nigeria) > en-ZA (South Africa) > en-GH (Ghana) >
 *   en-KE (Kenya) > en-TZ (Tanzania) > en-CM (Cameroon) >
 *   en-GB (British — closer to West-African than en-US) >
 *   any non-US English > any English
 *
 * Features:
 *   - Async voice loading with onvoiceschanged cache
 *   - Markdown / HTML stripping before speaking
 *   - Sentence-level chunking so long texts never get cut off mid-word
 *   - Queue-based chunked playback with natural inter-sentence pause
 *   - Adjustable rate / Pitch 0.94 — warm, deliberate delivery
 */
import { useCallback, useEffect, useRef, useState } from 'react';

const supported =
  typeof window !== 'undefined' && 'speechSynthesis' in window;

// African / British English BCP-47 codes in preference order
const PREFERRED_LANGS = [
  'en-NG', 'en-ZA', 'en-GH', 'en-KE', 'en-TZ', 'en-UG', 'en-CM', 'en-GB',
];
const DEFAULT_SPEECH_RATE = 0.92;

// ── Text preprocessing ────────────────────────────────────────────────────────

function cleanText(raw) {
  if (!raw) return '';
  return raw
    // strip markdown bold/italic/headers/code
    .replace(/#{1,6}\s+/g, '')
    .replace(/\*{1,3}([^*]+)\*{1,3}/g, '$1')
    .replace(/_([^_]+)_/g, '$1')
    .replace(/`[^`]*`/g, '')
    .replace(/```[\s\S]*?```/g, '')
    // strip HTML tags
    .replace(/<[^>]+>/g, ' ')
    // strip URLs
    .replace(/https?:\/\/\S+/g, '')
    // collapse bullets / list markers
    .replace(/^[\s]*[-*•]\s+/gm, '')
    // collapse multiple whitespace / newlines
    .replace(/\s{2,}/g, ' ')
    .trim();
}

/** Split cleaned text into sentence-sized chunks (≤ 200 chars each). */
function chunkText(text, maxLen = 170) {
  if (!text) return [];
  // Split on sentence and soft-pause punctuation so the voice does not rush lists.
  const raw = text.split(/(?<=[.!?;:])\s+|(?<=,)\s+/);
  const chunks = [];
  let current = '';
  for (const part of raw) {
    if ((current + ' ' + part).trim().length <= maxLen) {
      current = current ? current + ' ' + part : part;
    } else {
      if (current) chunks.push(current.trim());
      // If a single part is too long, break it at word boundaries
      if (part.length > maxLen) {
        const words = part.split(' ');
        let sub = '';
        for (const w of words) {
          if ((sub + ' ' + w).trim().length <= maxLen) {
            sub = sub ? sub + ' ' + w : w;
          } else {
            if (sub) chunks.push(sub.trim());
            sub = w;
          }
        }
        if (sub) chunks.push(sub.trim());
        current = '';
      } else {
        current = part;
      }
    }
  }
  if (current) chunks.push(current.trim());
  return chunks.filter(Boolean);
}

function pauseForChunk(text) {
  if (/[.!?]$/.test(text)) return 420;
  if (/[;:]$/.test(text)) return 320;
  if (/,$/.test(text)) return 220;
  return 160;
}

// ── Voice selection ───────────────────────────────────────────────────────────

function pickVoice(preferredLang) {
  if (!supported) return null;
  const voices = window.speechSynthesis.getVoices();
  if (!voices.length) return null;

  if (preferredLang) {
    const preferred = preferredLang.toLowerCase();
    const exact = voices.find(v => v.lang.toLowerCase() === preferred);
    if (exact) return exact;
    const partial = voices.find(v => v.lang.toLowerCase().startsWith(preferred));
    if (partial) return partial;
  }

  // 1. Exact match on preferred African / British codes
  for (const lang of PREFERRED_LANGS) {
    const v = voices.find(v => v.lang === lang);
    if (v) return v;
  }
  // 2. Partial match (e.g. 'en-NG-x-ioned')
  for (const lang of PREFERRED_LANGS) {
    const prefix = lang.toLowerCase();
    const v = voices.find(v => v.lang.toLowerCase().startsWith(prefix));
    if (v) return v;
  }
  // 3. Any non-US English voice
  const nonUS = voices.find(v => v.lang.startsWith('en-') && v.lang !== 'en-US');
  if (nonUS) return nonUS;
  // 4. Any English voice
  return voices.find(v => v.lang.startsWith('en')) || null;
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useSpeech() {
  const [speaking, setSpeaking]   = useState(false);
  const voiceRef   = useRef(null);   // cached voice
  const langRef    = useRef('en-NG');
  const queueRef   = useRef([]);     // pending sentence chunks
  const activeRef  = useRef(false);  // true while playback loop is running
  const cancelRef  = useRef(false);  // set to true on stop()
  const rateRef    = useRef(DEFAULT_SPEECH_RATE);

  // Pre-load voices as soon as they're available (async in most browsers)
  useEffect(() => {
    if (!supported) return;

    const load = () => {
      voiceRef.current = pickVoice();
    };
    load();
    window.speechSynthesis.onvoiceschanged = load;

    return () => {
      window.speechSynthesis.cancel();
      window.speechSynthesis.onvoiceschanged = null;
    };
  }, []);

  // ── Internal: speak one sentence chunk then advance queue ──────────────────
  const _speakNext = useCallback(() => {
    if (cancelRef.current || queueRef.current.length === 0) {
      setSpeaking(false);
      activeRef.current = false;
      return;
    }

    const text = queueRef.current.shift();
    const utt  = new SpeechSynthesisUtterance(text);

    // Apply voice
    const voice = pickVoice(langRef.current) || voiceRef.current || pickVoice();
    if (voice) {
      utt.voice = voice;
      utt.lang  = voice.lang;
    } else {
      utt.lang = langRef.current || 'en-NG';
    }

    // Warm, deliberate delivery that still lets users increase playback speed.
    utt.rate  = rateRef.current;
    utt.pitch = 0.94;

    utt.onstart = () => setSpeaking(true);
    utt.onend   = () => {
      if (cancelRef.current) {
        setSpeaking(false);
        activeRef.current = false;
        return;
      }
      // Natural punctuation-aware pause before next chunk
      if (queueRef.current.length > 0) {
        setTimeout(_speakNext, pauseForChunk(text));
      } else {
        setSpeaking(false);
        activeRef.current = false;
      }
    };
    utt.onerror = () => {
      setSpeaking(false);
      activeRef.current = false;
    };

    window.speechSynthesis.speak(utt);
  }, []);

  // ── Public API ──────────────────────────────────────────────────────────────

  const setRate = useCallback((rate) => {
    if (Number.isFinite(rate)) {
      rateRef.current = rate;
    }
  }, []);

  const speak = useCallback((rawText, preferredLang = 'en-NG', options = {}) => {
    if (!supported || !rawText) return;

    // Stop any current playback
    cancelRef.current = true;
    window.speechSynthesis.cancel();
    setSpeaking(false);

    const clean  = cleanText(rawText);
    const chunks = chunkText(clean);
    if (!chunks.length) return;

    queueRef.current  = chunks;
    langRef.current = preferredLang || 'en-NG';
    rateRef.current = Number.isFinite(options.rate) ? options.rate : DEFAULT_SPEECH_RATE;
    cancelRef.current = false;
    activeRef.current = true;

    // Small delay lets the browser finish the cancel() before starting new speech
    setTimeout(_speakNext, 80);
  }, [_speakNext]);

  const stop = useCallback(() => {
    cancelRef.current = true;
    if (supported) window.speechSynthesis.cancel();
    queueRef.current = [];
    setSpeaking(false);
    activeRef.current = false;
  }, []);

  return { speak, stop, speaking, supported, setRate };
}
