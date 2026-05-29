/**
 * SuggestedQuestions.jsx
 *
 * Welcome screen for the Chat AI:
 *  - Body-area quick-tap tiles — TOPICS, not scripts
 *    Mobile: 2-row horizontal scroll  |  Desktop: 3x4 grid
 *  - Pidgin / English / French starter chips
 *  - Quick shortcut pills
 */
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Thermometer, Wind, Stethoscope, Brain, Eye, Droplets,
  Baby, Leaf, MapPin, TrendingUp, HelpCircle, Heart, Bone, Shield,
} from 'lucide-react';

// Body-area tiles — send a plain symptom report so the AI asks follow-up questions
const BODY_TILES = [
  {
    icon: Thermometer,
    label: 'Fever / Hot body',
    emoji: '🌡️',
    msg: 'I have fever and my body is very hot',
    color: 'bg-red-50 border-red-200 text-red-700 dark:bg-red-950/30 dark:border-red-800 dark:text-red-300',
  },
  {
    icon: Brain,
    label: 'Head pain',
    emoji: '🤕',
    msg: 'I have a headache',
    color: 'bg-purple-50 border-purple-200 text-purple-700 dark:bg-purple-950/30 dark:border-purple-800 dark:text-purple-300',
  },
  {
    icon: Stethoscope,
    label: 'Stomach / Belle',
    emoji: '🤢',
    msg: 'I have stomach pain and I am vomiting',
    color: 'bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-950/30 dark:border-emerald-800 dark:text-emerald-300',
  },
  {
    icon: Wind,
    label: 'Cough / Breathing',
    emoji: '😮‍💨',
    msg: 'I have a cough and difficulty breathing',
    color: 'bg-sky-50 border-sky-200 text-sky-700 dark:bg-sky-950/30 dark:border-sky-800 dark:text-sky-300',
  },
  {
    icon: Eye,
    label: 'Skin / Eyes',
    emoji: '👁️',
    msg: 'I have a skin rash and my eyes are red and itchy',
    color: 'bg-amber-50 border-amber-200 text-amber-700 dark:bg-amber-950/30 dark:border-amber-800 dark:text-amber-300',
  },
  {
    icon: Droplets,
    label: 'Urinary / Pelvic',
    emoji: '💧',
    msg: 'I have pain when urinating and lower belly pain',
    color: 'bg-pink-50 border-pink-200 text-pink-700 dark:bg-pink-950/30 dark:border-pink-800 dark:text-pink-300',
  },
  {
    icon: Baby,
    label: 'My child is sick',
    emoji: '👶',
    msg: 'My child has fever and has been vomiting',
    color: 'bg-rose-50 border-rose-200 text-rose-700 dark:bg-rose-950/30 dark:border-rose-800 dark:text-rose-300',
  },
  {
    icon: Leaf,
    label: 'Traditional remedy',
    emoji: '🌿',
    msg: 'What traditional herbs or home remedies can help with common illnesses in Cameroon?',
    color: 'bg-green-50 border-green-200 text-green-700 dark:bg-green-950/30 dark:border-green-800 dark:text-green-300',
  },
  {
    icon: Heart,
    label: 'Chest / Heart',
    emoji: '❤️',
    msg: 'I have chest pain and shortness of breath',
    color: 'bg-red-50 border-red-200 text-red-600 dark:bg-red-950/30 dark:border-red-800 dark:text-red-300',
  },
  {
    icon: Bone,
    label: 'Joints / Bones',
    emoji: '🦴',
    msg: 'I have joint pain and body aches all over',
    color: 'bg-orange-50 border-orange-200 text-orange-700 dark:bg-orange-950/30 dark:border-orange-800 dark:text-orange-300',
  },
  {
    icon: Shield,
    label: 'STIs / Sexual Health',
    emoji: '🔴',
    msg: 'What are the signs of sexually transmitted infections (STIs) and how can I protect myself?',
    color: 'bg-fuchsia-50 border-fuchsia-200 text-fuchsia-700 dark:bg-fuchsia-950/30 dark:border-fuchsia-800 dark:text-fuchsia-300',
  },
  {
    icon: Stethoscope,
    label: 'Anus / Rectal pain',
    emoji: '🩸',
    msg: 'I have pain near my anus and sometimes see blood when I pass stool',
    color: 'bg-red-50 border-red-300 text-red-800 dark:bg-red-950/30 dark:border-red-700 dark:text-red-300',
  },
];

// Quick starter chips
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
    label: '🇬🇧 English',
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

export default function SuggestedQuestions({ onSelectQuestion }) {
  const [activeGroup, setActiveGroup] = useState(0);

  return (
    <div className="space-y-3 w-full">

      {/* Body-area tiles */}
      <div>
        <p className="text-[10px] sm:text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-0.5">
          Tap where it hurts — no typing needed
        </p>

        {/* MOBILE: 2-row horizontal scroll */}
        <div className="sm:hidden overflow-x-auto pb-1.5 -mx-0.5 px-0.5">
          <div
            className="gap-2"
            style={{
              display: 'grid',
              gridTemplateRows: 'repeat(2, auto)',
              gridAutoFlow: 'column',
              gridAutoColumns: 'minmax(120px, 135px)',
            }}
          >
            {BODY_TILES.map((tile) => (
              <motion.button
                key={tile.label}
                type="button"
                whileTap={{ scale: 0.93 }}
                onClick={() => onSelectQuestion(tile.msg)}
                className={`flex flex-col items-center gap-1.5 rounded-xl border-2 p-2.5 transition-all cursor-pointer text-center ${tile.color}`}
              >
                <span className="text-xl leading-none">{tile.emoji}</span>
                <span className="text-[11px] font-semibold leading-tight">{tile.label}</span>
              </motion.button>
            ))}
          </div>
        </div>

        {/* DESKTOP: 4-column grid */}
        <div className="hidden sm:grid sm:grid-cols-4 gap-2">
          {BODY_TILES.map((tile) => (
            <motion.button
              key={tile.label}
              type="button"
              whileHover={{ y: -2, scale: 1.02 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onSelectQuestion(tile.msg)}
              className={`flex flex-col items-center gap-1.5 rounded-xl border-2 p-3 transition-all cursor-pointer text-center ${tile.color}`}
            >
              <span className="text-xl leading-none">{tile.emoji}</span>
              <span className="text-xs font-semibold leading-tight">{tile.label}</span>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Chip groups */}
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
