/**
 * SeasonalBanner.jsx
 * Shows current-month disease alerts + sensitisation tips for Bamenda, NW Cameroon.
 * Fetches from /seasonal-context on mount; falls back to local data
 * so it works offline or when the backend is down.
 */
import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, X, Info, CloudRain, Sun, Wind, ShieldCheck, ChevronDown, ChevronUp } from 'lucide-react';

// ── Local fallback data with sensitisation tips ─────────────────────────────
const LOCAL_SEASONAL_RISKS = {
  1: {
    icon: Wind,
    high: ['Meningitis', 'Measles'],
    tip: 'Dry harmattan season — meningitis risk is high in NW Cameroon.',
    safeTips: [
      'Get vaccinated against meningitis (MenACWY) if not already done',
      'Seek urgent care immediately for stiff neck + high fever',
      'Avoid overcrowded dusty spaces; wear a face covering outdoors',
      'Ensure children up to 5 years are up-to-date on measles vaccination',
      'Drink plenty of water — harmattan dehydrates quickly',
    ],
    color: 'red',
  },
  2: {
    icon: Wind,
    high: ['Meningitis', 'Measles'],
    tip: 'Peak meningitis month — stiff neck with fever is a medical emergency.',
    safeTips: [
      'Meningitis vaccination is the best protection — confirm yours today',
      'Do NOT ignore stiff neck + fever + sensitivity to light — go to hospital immediately',
      'Isolate suspected measles cases and inform a health worker',
      'Keep indoor spaces ventilated; dust from harmattan worsens respiratory spread',
      'Boost immunity: eat nutritious food and stay hydrated',
    ],
    color: 'red',
  },
  3: {
    icon: Wind,
    high: ['Meningitis'],
    tip: 'End of harmattan — meningitis risk remains. Rainy season starts soon.',
    safeTips: [
      'Continue wearing face coverings outdoors in dry, dusty conditions',
      'Confirm meningitis vaccination status for all household members',
      'Prepare mosquito nets and repellents as rainy season approaches',
      'Clear stagnant water around your home before the rains begin',
      'Visit a health centre for a wellness check before the season changes',
    ],
    color: 'red',
  },
  4: {
    icon: CloudRain,
    high: ['Malaria', 'Typhoid Fever'],
    tip: 'Rainy season begins — sleep under a mosquito net and drink only clean water.',
    safeTips: [
      'Hang and use an insecticide-treated mosquito net every night',
      'Drain or cover all standing water near your home (mosquito breeding sites)',
      'Drink only boiled, filtered, or treated water to prevent typhoid',
      'Wash hands thoroughly with soap before eating and after using the toilet',
      'Any fever lasting more than 24 hours — get a malaria rapid test immediately',
    ],
    color: 'green',
  },
  5: {
    icon: CloudRain,
    high: ['Malaria', 'Typhoid Fever'],
    tip: 'Peak malaria month — any fever needs a malaria test the same day.',
    safeTips: [
      'Do NOT self-medicate for fever — test first, treat correctly',
      'Sleep under a net every night without exception',
      'Avoid roadside food and drinks of unknown origin (typhoid risk)',
      'Cover water storage containers tightly at all times',
      'Encourage children to complete the full malaria treatment course if prescribed',
    ],
    color: 'green',
  },
  6: {
    icon: CloudRain,
    high: ['Malaria', 'Cholera'],
    tip: 'High malaria & cholera season — purify all water, use bed nets.',
    safeTips: [
      'Boil or use water purification tablets for ALL drinking water',
      'Wash hands frequently, especially before eating and after using toilets',
      'Report any sudden watery diarrhoea to a health centre immediately (cholera sign)',
      'Use insecticide-treated bed nets and sleep windows closed',
      'Avoid open defecation — it directly contaminates community water sources',
    ],
    color: 'blue',
  },
  7: {
    icon: CloudRain,
    high: ['Malaria'],
    tip: 'Malaria season continues — test quickly for any fever, do not delay.',
    safeTips: [
      'Early treatment saves lives — test within 24 hours of fever onset',
      'Re-treat your nets with insecticide if they are older than 2 years',
      'Clear overgrown vegetation and fill pot-holes that hold water near your home',
      'Pregnant women must take malaria prophylaxis as prescribed (IPTp)',
      'Keep children away from stagnant water play areas',
    ],
    color: 'green',
  },
  8: {
    icon: CloudRain,
    high: ['Malaria', 'Cholera'],
    tip: 'Heavy rains — malaria & waterborne disease risk is at its peak.',
    safeTips: [
      'Boil all drinking water and keep it covered in clean containers',
      'Do not wash food or dishes in river or stream water during heavy rains',
      'Sleep every night under a mosquito net — even if it feels cool',
      'Report community outbreaks of diarrhoea or vomiting to the nearest health post',
      'Apply mosquito repellent to exposed skin in the evenings',
    ],
    color: 'blue',
  },
  9: {
    icon: CloudRain,
    high: ['Malaria', 'Cholera'],
    tip: 'Peak cholera risk month — boil or treat every drop of drinking water.',
    safeTips: [
      'Cholera spreads through contaminated water — boil ALL drinking water',
      'Oral Rehydration Salts (ORS) can save a life during severe diarrhoea',
      'Seek care urgently for rice-water stools — this is a cholera emergency',
      'Use pit latrines or proper sanitation; open defecation kills communities',
      'Continue malaria net use — both diseases are active this month',
    ],
    color: 'blue',
  },
  10: {
    icon: CloudRain,
    high: ['Malaria', 'Cholera'],
    tip: 'Rains ending — malaria and cholera still elevated. Stay vigilant.',
    safeTips: [
      'Continue water treatment even as rains slow — contamination persists',
      'Clear all stagnant pools as rains end to stop final malaria breeding',
      'Ensure the whole family completes full malaria treatment if prescribed',
      'Visit a health centre for deworming — rains increase intestinal worm risk',
      'Begin preparing for harmattan: stock vitamin C-rich foods for immunity',
    ],
    color: 'blue',
  },
  11: {
    icon: Wind,
    high: ['Common Cold', 'Meningitis'],
    tip: 'Harmattan begins — respiratory infections rising. Protect yourself from dust.',
    safeTips: [
      'Cover your nose and mouth when outdoors in dusty conditions',
      'Keep windows slightly closed at night to reduce harmattan cold air',
      'Drink warm fluids (herbal teas, warm water with lemon) to soothe the throat',
      'Start checking meningitis vaccination status — season is approaching',
      'Wash hands regularly to prevent spreading respiratory infections',
    ],
    color: 'amber',
  },
  12: {
    icon: Wind,
    high: ['Meningitis', 'Common Cold'],
    tip: 'Harmattan season — cold, dry air increases meningitis and cold risks.',
    safeTips: [
      'Get meningitis vaccination before January if not yet vaccinated',
      'Keep children warm at night — harmattan cold can cause severe chest infections',
      'Avoid sharing cups, towels, or utensils during this season',
      'Increase fluid intake — harmattan air causes rapid dehydration',
      'Report stiff neck + fever + severe headache as an emergency — do not wait',
    ],
    color: 'red',
  },
};

const MONTH_NAMES = [
  '', 'January','February','March','April','May','June',
  'July','August','September','October','November','December',
];

const COLOR_THEMES = {
  red: {
    banner:  'bg-red-50 border-red-300 text-red-900 dark:bg-red-950/40 dark:border-red-700 dark:text-red-200',
    icon:    'text-red-600 dark:text-red-400',
    chip:    'border-red-400/40 bg-red-100/60 dark:bg-red-900/30',
    tipBg:   'bg-red-100/70 dark:bg-red-900/30',
    tipIcon: 'text-red-600 dark:text-red-300',
    dot:     'bg-red-500',
  },
  green: {
    banner:  'bg-emerald-50 border-emerald-300 text-emerald-900 dark:bg-emerald-950/40 dark:border-emerald-700 dark:text-emerald-200',
    icon:    'text-emerald-600 dark:text-emerald-400',
    chip:    'border-emerald-400/40 bg-emerald-100/60 dark:bg-emerald-900/30',
    tipBg:   'bg-emerald-100/70 dark:bg-emerald-900/30',
    tipIcon: 'text-emerald-600 dark:text-emerald-300',
    dot:     'bg-emerald-500',
  },
  blue: {
    banner:  'bg-blue-50 border-blue-300 text-blue-900 dark:bg-blue-950/40 dark:border-blue-700 dark:text-blue-200',
    icon:    'text-blue-600 dark:text-blue-400',
    chip:    'border-blue-400/40 bg-blue-100/60 dark:bg-blue-900/30',
    tipBg:   'bg-blue-100/70 dark:bg-blue-900/30',
    tipIcon: 'text-blue-600 dark:text-blue-300',
    dot:     'bg-blue-500',
  },
  amber: {
    banner:  'bg-amber-50 border-amber-300 text-amber-900 dark:bg-amber-950/40 dark:border-amber-700 dark:text-amber-200',
    icon:    'text-amber-600 dark:text-amber-400',
    chip:    'border-amber-400/40 bg-amber-100/60 dark:bg-amber-900/30',
    tipBg:   'bg-amber-100/70 dark:bg-amber-900/30',
    tipIcon: 'text-amber-600 dark:text-amber-300',
    dot:     'bg-amber-500',
  },
};

export default function SeasonalBanner({ className = '', compact = false }) {
  const [data, setData]           = useState(null);
  const [visible, setVisible]     = useState(true);
  const [expanded, setExpanded]   = useState(false);   // for compact mode expand

  // Auto-dismiss after 8 s (full) / 12 s (compact)
  useEffect(() => {
    const delay = compact ? 12000 : 8000;
    const timer = setTimeout(() => setVisible(false), delay);
    return () => clearTimeout(timer);
  }, [compact]);

  useEffect(() => {
    const month = new Date().getMonth() + 1;
    const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    fetch(`${apiBase}/seasonal-context`)
      .then(r => r.ok ? r.json() : null)
      .then(json => {
        if (json && json.risks?.length) {
          setData({ ...json, _local: LOCAL_SEASONAL_RISKS[month] });
        } else throw new Error('empty');
      })
      .catch(() => {
        const local = LOCAL_SEASONAL_RISKS[month];
        if (local) {
          setData({
            month,
            month_name: MONTH_NAMES[month],
            banner_text: `⚠️ ${MONTH_NAMES[month]} in Bamenda: High risk of ${local.high.join(' & ')}. ${local.tip}`,
            risks: local.high.map(d => ({ disease: d, risk: 'high', reason: local.tip })),
            _local: local,
          });
        }
      });
  }, []);

  if (!data || !visible || !data.risks?.length) return null;

  const highRisks = data.risks.filter(r => r.risk === 'high');
  const month     = data.month || (new Date().getMonth() + 1);
  const local     = data._local || LOCAL_SEASONAL_RISKS[month];
  const Icon      = local?.icon || AlertTriangle;
  const colorKey  = local?.color || 'amber';
  const theme     = COLOR_THEMES[colorKey];

  // ── COMPACT mode (used in ChatAI header) ──────────────────────────────────
  if (compact) {
    return (
      <AnimatePresence>
        {visible && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className={`rounded-lg border ${theme.banner} ${className}`}
          >
            {/* Collapsed strip */}
            <div className="flex items-center gap-2 px-3 py-2">
              <Icon className={`h-3.5 w-3.5 shrink-0 ${theme.icon}`} />
              <span className="flex-1 text-xs font-medium truncate">
                {highRisks.map(r => r.disease).join(' & ')} alert — {data.month_name}
              </span>
              <button
                onClick={() => setExpanded(v => !v)}
                className={`shrink-0 opacity-60 hover:opacity-100 ${theme.icon}`}
                title="See safety tips"
              >
                {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              </button>
              <button onClick={() => setVisible(false)} className="shrink-0 opacity-40 hover:opacity-80">
                <X className="h-3 w-3" />
              </button>
            </div>
            {/* Expandable safety tips */}
            <AnimatePresence>
              {expanded && local?.safeTips && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <div className={`px-3 pb-2.5 pt-1 ${theme.tipBg} rounded-b-lg`}>
                    <p className="text-[10px] font-semibold uppercase tracking-wide mb-1.5 flex items-center gap-1">
                      <ShieldCheck className={`h-3 w-3 ${theme.tipIcon}`} />
                      How to stay safe this {data.month_name}
                    </p>
                    <ul className="space-y-1">
                      {local.safeTips.slice(0, 3).map((tip, i) => (
                        <li key={i} className="flex items-start gap-1.5 text-[10px]">
                          <span className={`w-1.5 h-1.5 rounded-full mt-1 shrink-0 ${theme.dot}`} />
                          {tip}
                        </li>
                      ))}
                    </ul>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    );
  }

  // ── FULL mode (homepage, key pages) ─────────────────────────────────────
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.25 }}
          className={`relative rounded-xl border ${theme.banner} ${className}`}
        >
          {/* Dismiss */}
          <button
            onClick={() => setVisible(false)}
            className="absolute right-2 top-2 opacity-40 hover:opacity-100 transition-opacity"
            aria-label="Dismiss seasonal alert"
          >
            <X className="h-4 w-4" />
          </button>

          {/* Header */}
          <div className="px-4 pt-3 pb-2">
            <div className="flex items-center gap-2 mb-2">
              <Icon className={`h-5 w-5 shrink-0 ${theme.icon}`} />
              <span className="font-bold text-sm">
                {data.month_name} Health Alert — Bamenda, NW Cameroon
              </span>
            </div>

            {/* Disease chips */}
            <div className="flex flex-wrap gap-1.5 mb-2">
              {highRisks.map(r => (
                <span
                  key={r.disease}
                  className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${theme.chip}`}
                >
                  <AlertTriangle className="h-2.5 w-2.5" />
                  {r.disease}
                </span>
              ))}
            </div>

            {/* Risk reasons */}
            <div className="space-y-0.5">
              {highRisks.map(r => (
                <p key={r.disease} className="text-[11px] opacity-80">
                  <strong>{r.disease}:</strong> {r.reason}
                </p>
              ))}
            </div>
          </div>

          {/* Safety Tips Section */}
          {local?.safeTips && (
            <div className={`mx-3 mb-3 rounded-lg px-3 py-2.5 ${theme.tipBg}`}>
              <p className={`text-[11px] font-bold uppercase tracking-wide mb-2 flex items-center gap-1.5 ${theme.tipIcon}`}>
                <ShieldCheck className="h-3.5 w-3.5" />
                How to stay safe this {data.month_name}
              </p>
              <ul className="space-y-1.5">
                {local.safeTips.map((tip, i) => (
                  <li key={i} className="flex items-start gap-2 text-[11px]">
                    <span className={`w-1.5 h-1.5 rounded-full mt-[4px] shrink-0 ${theme.dot}`} />
                    <span className="leading-relaxed">{tip}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Footer hint */}
          <div className="flex items-start gap-1.5 text-[10px] opacity-65 px-4 pb-3">
            <Info className="h-3 w-3 shrink-0 mt-0.5" />
            <span>Describe any symptoms early in the chat for faster, season-aware guidance.</span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
