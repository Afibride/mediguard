/**
 * SpeakButton — reads aloud the given `text` using the browser's SpeechSynthesis API.
 * Hidden when the API is not available (older browsers).
 *
 * Props:
 *   text      — string to read aloud
 *   lang      — BCP-47 tag, e.g. 'en-US' or 'fr-FR'
 *   size      — 'sm' | 'md' (default 'md')
 *   className — extra CSS classes
 *   label     — optional visible label shown next to the icon
 */
import React from 'react';
import { Volume2, VolumeX } from 'lucide-react';
import { motion } from 'framer-motion';
import { useSpeech } from '@/hooks/use-speech';
import { useLanguage } from '@/contexts/LanguageContext';

const LANG_MAP = { en: 'en-US', fr: 'fr-FR' };

export default function SpeakButton({ text, lang, size = 'md', className = '', label }) {
  const { speak, stop, speaking, supported } = useSpeech();
  const { lang: appLang } = useLanguage();
  const resolvedLang = lang || LANG_MAP[appLang] || 'en-US';

  if (!supported) return null;

  const sizeMap = {
    sm: { btn: 'h-7 w-7', icon: 'h-3.5 w-3.5' },
    md: { btn: 'h-9 w-9', icon: 'h-4 w-4' },
  };
  const s = sizeMap[size] || sizeMap.md;

  const handleClick = () => {
    if (speaking) {
      stop();
    } else {
      speak(text, resolvedLang);
    }
  };

  return (
    <motion.button
      type="button"
      title={speaking ? 'Stop reading' : 'Read aloud'}
      aria-label={speaking ? 'Stop reading aloud' : 'Read aloud'}
      onClick={handleClick}
      whileTap={{ scale: 0.9 }}
      className={`
        inline-flex items-center gap-1.5 rounded-lg border transition-all duration-200 shrink-0
        ${label ? 'px-3 py-1.5' : `${s.btn} justify-center`}
        ${speaking
          ? 'bg-primary border-primary text-primary-foreground shadow-md shadow-primary/30'
          : 'bg-background border-input hover:border-primary hover:text-primary text-muted-foreground'
        }
        ${className}
      `}
    >
      {speaking
        ? <VolumeX className={s.icon} />
        : <Volume2 className={s.icon} />
      }
      {label && <span className="text-xs font-medium">{speaking ? 'Stop' : label}</span>}
    </motion.button>
  );
}
