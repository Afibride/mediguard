/**
 * VoiceInput.jsx
 * A microphone button that uses the browser's Web Speech API to capture
 * spoken input and pass the transcript to the parent via onTranscript().
 *
 * Works in Chrome, Edge, and most Android browsers.
 * Falls back gracefully (button hidden) when the API is unavailable.
 *
 * Props:
 *   onTranscript(text)   — called with the final transcript string
 *   onListening(bool)    — optional, called when listening state changes
 *   lang                 — BCP-47 language tag, default 'en-US'
 *                          Pass 'fr-FR' for French, 'en-NG' for Nigerian/Cameroonian English
 *   disabled             — disables the button
 *   className            — extra CSS classes on the button
 *   size                 — 'sm' | 'md' (default 'md')
 */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Mic, MicOff, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Check once whether the browser supports the API
const SpeechRecognition =
  typeof window !== 'undefined'
    ? window.SpeechRecognition || window.webkitSpeechRecognition || null
    : null;

export default function VoiceInput({
  onTranscript,
  onListening,
  lang = 'en-US',
  disabled = false,
  className = '',
  size = 'md',
}) {
  const [supported]  = useState(() => !!SpeechRecognition);
  const [listening,  setListening]  = useState(false);
  const [error,      setError]      = useState('');
  const recognizer                  = useRef(null);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      try { recognizer.current?.stop(); } catch {}
    };
  }, []);

  const startListening = useCallback(() => {
    if (!SpeechRecognition || disabled) return;
    setError('');

    const rec = new SpeechRecognition();
    rec.lang = lang;
    rec.interimResults  = false;
    rec.maxAlternatives = 1;
    rec.continuous      = false;

    rec.onstart = () => {
      setListening(true);
      onListening?.(true);
    };

    rec.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      onTranscript(transcript);
    };

    rec.onerror = (event) => {
      if (event.error === 'no-speech') {
        setError('No speech detected. Try again.');
      } else if (event.error === 'not-allowed') {
        setError('Microphone access denied. Allow mic in your browser settings.');
      } else {
        setError('Voice input failed. Try typing instead.');
      }
    };

    rec.onend = () => {
      setListening(false);
      onListening?.(false);
    };

    recognizer.current = rec;
    rec.start();
  }, [disabled, lang, onTranscript, onListening]);

  const stopListening = useCallback(() => {
    try { recognizer.current?.stop(); } catch {}
    setListening(false);
    onListening?.(false);
  }, [onListening]);

  // Hidden entirely when not supported (older browsers)
  if (!supported) return null;

  const sizeMap = {
    sm: { btn: 'h-8 w-8', icon: 'h-3.5 w-3.5' },
    md: { btn: 'h-10 w-10 sm:h-11 sm:w-11', icon: 'h-4 w-4 sm:h-5 sm:w-5' },
  };
  const s = sizeMap[size] || sizeMap.md;

  return (
    <div className="relative inline-flex flex-col items-center">
      <motion.button
        type="button"
        title={listening ? 'Stop listening' : 'Speak your symptoms (voice input)'}
        onClick={listening ? stopListening : startListening}
        disabled={disabled}
        whileTap={{ scale: 0.92 }}
        className={`
          relative ${s.btn} rounded-lg flex items-center justify-center
          border transition-all duration-200 shrink-0
          ${listening
            ? 'bg-red-500 border-red-400 text-white shadow-lg shadow-red-500/40'
            : 'bg-background border-input hover:border-primary hover:text-primary text-muted-foreground'
          }
          disabled:opacity-40 disabled:cursor-not-allowed
          ${className}
        `}
      >
        {/* Pulsing ring when active */}
        {listening && (
          <motion.span
            className="absolute inset-0 rounded-lg border-2 border-red-400"
            animate={{ scale: [1, 1.35], opacity: [0.8, 0] }}
            transition={{ duration: 1.1, repeat: Infinity, ease: 'easeOut' }}
          />
        )}
        {listening
          ? <MicOff className={s.icon} />
          : <Mic className={s.icon} />
        }
      </motion.button>

      {/* Error tooltip */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="absolute top-full mt-1.5 left-1/2 -translate-x-1/2 w-48 rounded-lg bg-destructive/90 text-white text-[10px] px-2 py-1.5 text-center z-20 shadow-lg"
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
