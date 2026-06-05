/**
 * SpeakButton — reads the given `text` aloud.
 *
 * Always shows a gentle pulsing ring so users know audio is available.
 * Pulses faster and glows when actively speaking.
 *
 * Props:
 *   text      — string to read aloud
 *   lang      — BCP-47 tag override (e.g. 'fr-FR')
 *   size      — 'sm' | 'md' (default 'md')
 *   className — extra CSS classes
 *   label     — optional visible label next to the icon
 */
import React from 'react';
import { Volume2, VolumeX } from 'lucide-react';
import { useSpeech } from '@/hooks/use-speech';
import { useLanguage } from '@/contexts/LanguageContext';

const LANG_MAP = { en: 'en-NG', fr: 'fr-FR' };

export default function SpeakButton({ text, lang, size = 'md', className = '', label }) {
  const { speak, stop, speaking, supported } = useSpeech();
  const { lang: appLang } = useLanguage();

  if (!supported) return null;

  const resolvedLang = lang || LANG_MAP[appLang] || 'en-NG';
  const s = size === 'sm'
    ? { btn: 'h-7 w-7', icon: 'h-3.5 w-3.5', ring: 'h-9 w-9' }
    : { btn: 'h-9 w-9', icon: 'h-4 w-4',   ring: 'h-11 w-11' };

  const handleClick = () => speaking ? stop() : speak(text, resolvedLang);

  return (
    <span
      className={`relative inline-flex items-center justify-center shrink-0 ${label ? '' : s.ring} ${className}`}
      style={{ isolation: 'isolate' }}
    >
      {/* Idle pulse ring — always visible so users see audio is available */}
      {!speaking && (
        <span
          className={`
            absolute inset-0 rounded-full
            block
          `}
          style={{
            background: 'radial-gradient(circle, hsl(var(--primary)/0.18) 0%, transparent 70%)',
            animation: 'mg-speak-idle 2.4s ease-in-out infinite',
          }}
        />
      )}

      {/* Active pulse ring — faster glow when speaking */}
      {speaking && (
        <>
          <span
            className="absolute inset-0 rounded-full border-2 border-primary/60"
            style={{ animation: 'mg-speak-active 0.9s ease-in-out infinite' }}
          />
          <span
            className="absolute inset-0 rounded-full bg-primary/10"
            style={{ animation: 'mg-speak-active 0.9s ease-in-out infinite 0.45s' }}
          />
        </>
      )}

      {/* Button itself */}
      <button
        type="button"
        title={speaking ? 'Stop reading' : 'Read aloud'}
        aria-label={speaking ? 'Stop reading aloud' : 'Read aloud'}
        onClick={handleClick}
        className={`
          relative z-10 inline-flex items-center gap-1.5 rounded-full border transition-all duration-200
          ${label ? 'px-3 py-1.5 rounded-lg' : `${s.btn} justify-center`}
          ${speaking
            ? 'bg-primary border-primary text-primary-foreground shadow-lg shadow-primary/40 scale-105'
            : 'bg-background border-primary/40 text-primary hover:border-primary hover:bg-primary/5 hover:scale-105'
          }
        `}
        style={speaking ? {} : {
          animation: 'mg-speak-button-blink 1.8s ease-in-out infinite',
          boxShadow: '0 0 0 2px hsl(var(--primary)/0.12)',
        }}
      >
        {speaking
          ? <VolumeX className={s.icon} />
          : <Volume2 className={s.icon} />
        }
        {label && (
          <span className="text-xs font-medium">{speaking ? 'Stop' : label}</span>
        )}
      </button>

      {/* Keyframes injected once */}
      <style>{`
        @keyframes mg-speak-idle {
          0%, 100% { opacity: 0.5; transform: scale(0.88); }
          50%       { opacity: 1;   transform: scale(1.08); }
        }
        @keyframes mg-speak-active {
          0%, 100% { opacity: 0.9; transform: scale(1);    }
          50%       { opacity: 0.3; transform: scale(1.22); }
        }
        @keyframes mg-speak-button-blink {
          0%, 100% { border-color: hsl(var(--primary)/0.40); filter: brightness(1); }
          50%      { border-color: hsl(var(--primary)/0.95); filter: brightness(1.08); }
        }
      `}</style>
    </span>
  );
}
