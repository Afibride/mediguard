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
  Thermometer, Wind, Stethoscope, Brain, Eye, Droplets,
  Baby, Leaf, MapPin, TrendingUp, HelpCircle, Heart, Bone, Shield,
} from 'lucide-react';

// Each tile has a `prompt` — the clarifying question the bot asks when tapped.
// `childCard` activates child mode automatically.
// `remedyCard` marks the traditional remedy card.
const BODY_TILES = [
  {
    icon: Thermometer,
    label: 'Fever / Hot body',
    emoji: '🌡️',
    color: 'bg-red-50 border-red-200 text-red-700 dark:bg-red-950/30 dark:border-red-800 dark:text-red-300',
    prompt: "🌡️ **Fever & Body Heat**\n\nTo help you properly, please describe what you're experiencing:\n\n- How high is your temperature? (do you have a thermometer?)\n- How long have you had the fever?\n- Any other symptoms — chills, sweating, headache, body aches?",
    followUps: ['About 38°C for 2 days', '3 days with chills and sweating', 'High fever, no thermometer', 'Fever with severe headache'],
  },
  {
    icon: Brain,
    label: 'Head pain',
    emoji: '🤕',
    color: 'bg-purple-50 border-purple-200 text-purple-700 dark:bg-purple-950/30 dark:border-purple-800 dark:text-purple-300',
    prompt: "🤕 **Head Pain**\n\nPlease describe your headache so I can help better:\n\n- Where exactly does it hurt? (forehead, temples, back of head, all over?)\n- Is it throbbing, pressing, or sharp?\n- Did it come on suddenly or build up slowly?\n- Any other symptoms with it?",
    followUps: ['Throbbing on one side', 'Pressure across forehead', 'Sudden severe headache', 'Headache with fever and stiff neck'],
  },
  {
    icon: Stethoscope,
    label: 'Stomach / Belle',
    emoji: '🤢',
    color: 'bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-950/30 dark:border-emerald-800 dark:text-emerald-300',
    prompt: "🤢 **Stomach / Belly Symptoms**\n\nPlease describe what's happening in your stomach area:\n\n- Where exactly is the pain — upper belly, lower belly, or all over?\n- Do you have vomiting, diarrhoea, or constipation?\n- Did it start after eating?\n- How long has it been going on?",
    followUps: ['Pain after eating', 'Vomiting and diarrhoea', 'Lower belly pain', 'Burning in stomach'],
  },
  {
    icon: Wind,
    label: 'Cough / Breathing',
    emoji: '😮‍💨',
    color: 'bg-sky-50 border-sky-200 text-sky-700 dark:bg-sky-950/30 dark:border-sky-800 dark:text-sky-300',
    prompt: "😮‍💨 **Cough & Breathing**\n\nTell me more about your cough or breathing difficulty:\n\n- Is the cough dry, or does it produce phlegm (if so, what colour)?\n- Is there any difficulty breathing, chest pain, or wheezing?\n- How long have you had this?\n- Any fever or weight loss?",
    followUps: ['Dry cough for 2 weeks', 'Cough with yellow phlegm', 'Difficulty breathing', 'Cough with chest pain'],
  },
  {
    icon: Eye,
    label: 'Skin / Eyes',
    emoji: '👁️',
    color: 'bg-amber-50 border-amber-200 text-amber-700 dark:bg-amber-950/30 dark:border-amber-800 dark:text-amber-300',
    prompt: "👁️ **Skin & Eye Symptoms**\n\nPlease describe what you're seeing on your skin or in your eyes:\n\n- What does it look like? (rash, blisters, red spots, discharge?)\n- Where on the body — face, arms, groin, all over?\n- Is there itching, pain, or swelling?\n- Are your eyes red, discharging, or painful?",
    followUps: ['Itchy rash all over body', 'Red eye with discharge', 'Blisters on skin', 'Ring-shaped patch on skin'],
  },
  {
    icon: Droplets,
    label: 'Urinary / Pelvic',
    emoji: '💧',
    color: 'bg-pink-50 border-pink-200 text-pink-700 dark:bg-pink-950/30 dark:border-pink-800 dark:text-pink-300',
    prompt: "💧 **Urinary & Pelvic Symptoms**\n\nTo help you, please describe what you're experiencing:\n\n- Is there pain or burning when urinating?\n- Do you need to go to the toilet very frequently?\n- Any lower belly or pelvic pain?\n- Any unusual discharge or blood in urine?",
    followUps: ['Burning when urinating', 'Frequent urination', 'Blood in urine', 'Pelvic pain and discharge'],
  },
  {
    icon: Baby,
    label: 'My child is sick',
    emoji: '👶',
    color: 'bg-rose-50 border-rose-200 text-rose-700 dark:bg-rose-950/30 dark:border-rose-800 dark:text-rose-300',
    childCard: true,
    prompt: "👶 **Child Health — Mode Activated**\n\nI'm now in child health mode to give you age-appropriate guidance.\n\nPlease tell me:\n- **How old is the child?** (newborn / months / years)\n- **What symptoms do they have?** (fever, vomiting, rash, diarrhoea, difficulty breathing?)\n- **How long have the symptoms been going on?**",
    followUps: ['Fever and vomiting — 2 years old', 'Rash on body — 6 months old', 'Diarrhoea and won\'t drink — 1 year old', 'Fast breathing — 3 years old'],
  },
  {
    icon: Leaf,
    label: 'Traditional remedy',
    emoji: '🌿',
    color: 'bg-green-50 border-green-200 text-green-700 dark:bg-green-950/30 dark:border-green-800 dark:text-green-300',
    remedyCard: true,
    prompt: "🌿 **Traditional Remedies & Herbs**\n\nI can tell you what local plants and home remedies may help, and when you still need to go to a clinic.\n\nWhat symptom or condition are you looking for a remedy for?\n\n- Fever / malaria?\n- Stomach pain?\n- Cough?\n- Skin condition?\n- Something else?",
    followUps: ['Neem for fever', 'Bitter leaf for stomach pain', 'Garlic for cough', 'Moringa for weakness'],
  },
  {
    icon: Heart,
    label: 'Chest / Heart',
    emoji: '❤️',
    color: 'bg-red-50 border-red-200 text-red-600 dark:bg-red-950/30 dark:border-red-800 dark:text-red-300',
    prompt: "❤️ **Chest & Heart Symptoms**\n\nChest symptoms can be serious — please describe carefully:\n\n- Is it pain, tightness, pressure, or palpitations?\n- Does the pain spread to your arm, jaw, or back?\n- Is there shortness of breath?\n- Did it come on suddenly or build up?\n\n⚠️ *If you have crushing chest pain, call for help immediately.*",
    followUps: ['Chest pain spreading to arm', 'Heart racing / palpitations', 'Tight chest with breathlessness', 'Mild chest discomfort'],
  },
  {
    icon: Bone,
    label: 'Joints / Bones',
    emoji: '🦴',
    color: 'bg-orange-50 border-orange-200 text-orange-700 dark:bg-orange-950/30 dark:border-orange-800 dark:text-orange-300',
    prompt: "🦴 **Joint & Bone Pain**\n\nPlease describe your joint or body pain:\n\n- Which joints or areas are affected? (knees, wrists, hips, back, all over?)\n- Is there swelling, redness, or warmth at the joint?\n- Did it come on suddenly or gradually?\n- Any fever or rash along with the pain?",
    followUps: ['Both knees swollen and painful', 'Joint pain all over with fever', 'Back pain', 'Stiff joints in the morning'],
  },
  {
    icon: Shield,
    label: 'STIs / Sexual Health',
    emoji: '🔴',
    color: 'bg-fuchsia-50 border-fuchsia-200 text-fuchsia-700 dark:bg-fuchsia-950/30 dark:border-fuchsia-800 dark:text-fuchsia-300',
    prompt: "🔴 **Sexual Health & STIs**\n\nI can help with sexual health questions — all information is confidential.\n\nWhat would you like to know?\n\n- Signs and symptoms of a specific STI?\n- How to protect yourself?\n- Where to get tested in Bamenda?\n- Treatment options?\n- Or are you experiencing a specific symptom?",
    followUps: ['Signs of gonorrhea', 'Unusual discharge', 'Genital sore or blister', 'Where to test for STIs in Bamenda'],
  },
  {
    icon: Stethoscope,
    label: 'Anus / Rectal pain',
    emoji: '🩸',
    color: 'bg-red-50 border-red-300 text-red-800 dark:bg-red-950/30 dark:border-red-700 dark:text-red-300',
    prompt: "🩸 **Anal & Rectal Symptoms**\n\nPlease describe what you're experiencing:\n\n- Is there pain, bleeding, itching, or swelling near the anus?\n- Do you see blood — on the stool, on the paper, or in the toilet?\n- Is there a lump or swelling?\n- Any pain when passing stool?",
    followUps: ['Blood on toilet paper', 'Itching and swelling near anus', 'Pain when passing stool', 'Lump near anus'],
  },
];

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

export default function SuggestedQuestions({ onSelectQuestion, onSelectCard }) {
  const [activeGroup, setActiveGroup] = useState(0);

  return (
    <div className="space-y-3 w-full">

      {/* Body-area tiles */}
      <div>
        <p className="text-[10px] sm:text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-0.5">
          Tap where it hurts — tell me more
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
                onClick={() => onSelectCard(tile)}
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
              onClick={() => onSelectCard(tile)}
              className={`flex flex-col items-center gap-1.5 rounded-xl border-2 p-3 transition-all cursor-pointer text-center ${tile.color}`}
            >
              <span className="text-xl leading-none">{tile.emoji}</span>
              <span className="text-xs font-semibold leading-tight">{tile.label}</span>
            </motion.button>
          ))}
        </div>
      </div>

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
