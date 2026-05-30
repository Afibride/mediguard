/**
 * SuggestedQuestions.jsx
 *
 * Welcome screen for the Chat AI:
 *  - Body-area quick-tap tiles — clicking opens a clarifying bot prompt,
 *    NOT a direct AI query. The user then describes their specific symptom.
 *  - Pidgin / English / French starter chips (still send directly)
 *  - Quick shortcut pills
 */
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MapPin, TrendingUp, HelpCircle,
} from 'lucide-react';

// Quick starter chips — these still send directly to AI
const CHIP_GROUPS = [
  {
    label: '🗣️ Pidgin',
    chips: [
      'My head dey pain me and body dey hot',
      'Belle dey do me and I dey purge',
      'I dey cough strong strong',
      'My pikin no dey eat and dey hot',
      'Body weak, I no get strength',
      'I get pain for yansh area, blood dey come',
    ],
  },
  {
    label: 'EN English',
    chips: [
      'I have fever, headache and chills',
      'What are the symptoms of malaria?',
      'How is typhoid treated?',
      'Nearest hospital in Bamenda',
      'My child has a rash and fever',
      'What are signs of piles (hemorrhoids)?',
    ],
  },
  {
    label: '🇫🇷 Français',
    chips: [
      "J'ai de la fièvre et mal à la tête",
      "Quels sont les symptômes du paludisme?",
      "Comment traiter la typhoïde?",
      "Hôpital le plus proche à Bamenda",
      "Mon enfant a une éruption et de la fièvre",
      "Quels sont les signes des hémorroïdes?",
    ],
  },
];

export default function SuggestedQuestions({ onSelectQuestion, onSelectCard }) {
  const [activeGroup, setActiveGroup] = useState(0);

  return (
    <div className="space-y-3 w-full">

      {/* Traditional herbs suggested question */}
      <motion.button
        type="button"
        whileHover={{ y: -1, scale: 1.01 }}
        whileTap={{ scale: 0.97 }}
        onClick={() => onSelectQuestion('What traditional herbs or home remedies can help with common symptoms like fever, stomach pain, or cough?')}
        className="w-full flex items-center gap-3 rounded-xl border-2 border-green-200 bg-green-50 text-green-700 dark:bg-green-950/30 dark:border-green-800 dark:text-green-300 p-3 transition-all cursor-pointer text-left"
      >
        <span className="text-2xl leading-none flex-shrink-0">🌿</span>
        <div>
          <p className="text-xs font-semibold leading-snug">Ask about traditional herbs &amp; home remedies</p>
          <p className="text-[11px] opacity-75 leading-tight mt-0.5">Neem, bitter leaf, garlic, moringa &amp; more local plants</p>
        </div>
      </motion.button>

      {/* Chip groups — send directly to AI */}
      <div>
        <div className="flex gap-1.5 mb-2 overflow-x-auto hide-scrollbar">
          {CHIP_GROUPS.map((g, i) => (
            <button
              key={g.label}
              type="button"
              onClick={() => setActiveGroup(i)}
              className={`shrink-0 rounded-full border px-3 py-1 text-[11px] sm:text-xs font-medium transition-all ${
                activeGroup === i
                  ? 'bg-primary text-primary-foreground border-primary'
                  : 'bg-background text-muted-foreground border-border hover:border-primary/50'
              }`}
            >
              {g.label}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={activeGroup}
            initial={{ opacity: 0, x: 8 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -8 }}
            transition={{ duration: 0.15 }}
            className="flex gap-2 overflow-x-auto hide-scrollbar pb-1"
          >
            {CHIP_GROUPS[activeGroup].chips.map((chip) => (
              <motion.button
                key={chip}
                type="button"
                whileTap={{ scale: 0.96 }}
                onClick={() => onSelectQuestion(chip)}
                className="shrink-0 rounded-lg border border-primary/30 bg-primary/8 hover:bg-primary hover:text-primary-foreground hover:border-primary px-3 py-2 text-[11px] sm:text-xs font-medium text-primary transition-colors text-left max-w-[200px] sm:max-w-none"
              >
                "{chip}"
              </motion.button>
            ))}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Shortcut pills */}
      <div className="flex gap-2 overflow-x-auto hide-scrollbar pb-0.5">
        {[
          { icon: MapPin,     label: 'Nearest hospital', msg: 'Nearest hospital near me' },
          { icon: TrendingUp, label: 'Disease trends',   msg: 'What diseases are trending in Bamenda right now?' },
          { icon: HelpCircle, label: 'Vaccination',      msg: 'What is the vaccination schedule for children in Cameroon?' },
        ].map((s) => {
          const Icon = s.icon;
          return (
            <motion.button
              key={s.label}
              type="button"
              whileTap={{ scale: 0.96 }}
              onClick={() => onSelectQuestion(s.msg)}
              className="shrink-0 flex items-center gap-1.5 rounded-full border border-border hover:border-primary/50 bg-muted/40 hover:bg-muted px-3 py-1.5 text-[10px] sm:text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <Icon className="h-3 w-3" />
              {s.label}
            </motion.button>
          );
        })}
      </div>

    </div>
  );
}
