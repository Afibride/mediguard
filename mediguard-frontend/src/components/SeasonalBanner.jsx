/**
 * SeasonalBanner.jsx
 * Shows current-month disease alerts for Bamenda, NW Cameroon.
 * Fetches from /seasonal-context on mount; falls back to local data
 * so it works offline or when the backend is down.
 */
import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, X, Info, CloudRain, Sun, Wind } from 'lucide-react';

// ── Local fallback (mirrors backend _BAMENDA_SEASONAL_RISKS) ─────────────────
const LOCAL_SEASONAL_RISKS = {
  1:  { icon: Wind,      high: ["Meningitis", "Measles"],        tip: "Dry harmattan season — meningitis risk in NW Cameroon" },
  2:  { icon: Wind,      high: ["Meningitis", "Measles"],        tip: "Peak meningitis month — seek urgent care for stiff neck + fever" },
  3:  { icon: Wind,      high: ["Meningitis"],                   tip: "End of harmattan season — meningitis still a risk" },
  4:  { icon: CloudRain, high: ["Malaria", "Typhoid Fever"],     tip: "Rainy season starts — sleep under a net, drink clean water" },
  5:  { icon: CloudRain, high: ["Malaria", "Typhoid Fever"],     tip: "Peak malaria month — any fever needs a malaria test" },
  6:  { icon: CloudRain, high: ["Malaria", "Cholera"],           tip: "High malaria & cholera season — purify water, use nets" },
  7:  { icon: CloudRain, high: ["Malaria"],                      tip: "Malaria season continues — test quickly for fever" },
  8:  { icon: CloudRain, high: ["Malaria", "Cholera"],           tip: "Heavy rains — malaria & waterborne diseases high" },
  9:  { icon: CloudRain, high: ["Malaria", "Cholera"],           tip: "Peak cholera risk — boil/treat all drinking water" },
  10: { icon: CloudRain, high: ["Malaria", "Cholera"],           tip: "Rains ending — malaria & cholera still elevated" },
  11: { icon: Wind,      high: ["Common Cold"],                  tip: "Harmattan starts — respiratory infections rising" },
  12: { icon: Wind,      high: ["Meningitis", "Common Cold"],    tip: "Harmattan season — cold air & meningitis risk returning" },
};

const MONTH_NAMES = [
  '', 'January','February','March','April','May','June',
  'July','August','September','October','November','December',
];

export default function SeasonalBanner({ className = '', compact = false }) {
  const [data, setData]       = useState(null);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const month = new Date().getMonth() + 1;           // 1–12
    const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    fetch(`${apiBase}/seasonal-context`)
      .then(r => r.ok ? r.json() : null)
      .then(json => {
        if (json && json.risks?.length) {
          setData(json);
        } else {
          throw new Error('empty');
        }
      })
      .catch(() => {
        // Use local fallback
        const local = LOCAL_SEASONAL_RISKS[month];
        if (local) {
          setData({
            month,
            month_name: MONTH_NAMES[month],
            banner_text: `⚠️ ${MONTH_NAMES[month]} in Bamenda: High risk of ${local.high.join(' & ')}. ${local.tip}.`,
            risks: local.high.map(d => ({ disease: d, risk: 'high', reason: local.tip })),
          });
        }
      });
  }, []);

  if (!data || !visible || !data.risks?.length) return null;

  const highRisks = data.risks.filter(r => r.risk === 'high');
  const month     = data.month || (new Date().getMonth() + 1);
  const local     = LOCAL_SEASONAL_RISKS[month];
  const Icon      = local?.icon || AlertTriangle;

  // Colour theme by season
  const isMalariaSeason = highRisks.some(r => r.disease === 'Malaria');
  const isMeningitis    = highRisks.some(r => r.disease === 'Meningitis');
  const isWaterborne    = highRisks.some(r => ['Cholera','Typhoid Fever'].includes(r.disease));

  let colours = 'bg-amber-50 border-amber-300 text-amber-900 dark:bg-amber-950/40 dark:border-amber-700 dark:text-amber-200';
  let iconCol  = 'text-amber-600 dark:text-amber-400';
  if (isMeningitis) {
    colours = 'bg-red-50 border-red-300 text-red-900 dark:bg-red-950/40 dark:border-red-700 dark:text-red-200';
    iconCol = 'text-red-600 dark:text-red-400';
  } else if (isWaterborne) {
    colours = 'bg-blue-50 border-blue-300 text-blue-900 dark:bg-blue-950/40 dark:border-blue-700 dark:text-blue-200';
    iconCol = 'text-blue-600 dark:text-blue-400';
  }

  if (compact) {
    return (
      <AnimatePresence>
        {visible && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-xs ${colours} ${className}`}
          >
            <Icon className={`h-3.5 w-3.5 shrink-0 ${iconCol}`} />
            <span className="flex-1 truncate font-medium">
              {highRisks.map(r => r.disease).join(' & ')} risk — {data.month_name}
            </span>
            <button onClick={() => setVisible(false)} className="shrink-0 opacity-50 hover:opacity-100">
              <X className="h-3 w-3" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    );
  }

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.25 }}
          className={`relative rounded-xl border px-4 py-3 ${colours} ${className}`}
        >
          {/* Dismiss */}
          <button
            onClick={() => setVisible(false)}
            className="absolute right-2 top-2 opacity-40 hover:opacity-100 transition-opacity"
          >
            <X className="h-4 w-4" />
          </button>

          {/* Header */}
          <div className="flex items-center gap-2 mb-2">
            <Icon className={`h-4 w-4 shrink-0 ${iconCol}`} />
            <span className="font-bold text-sm">
              {data.month_name} Health Alert — Bamenda
            </span>
          </div>

          {/* Disease chips */}
          <div className="flex flex-wrap gap-1.5 mb-2">
            {highRisks.map(r => (
              <span
                key={r.disease}
                className="inline-flex items-center gap-1 rounded-full border border-current/30 bg-white/40 dark:bg-black/20 px-2.5 py-0.5 text-[11px] font-semibold"
              >
                <AlertTriangle className="h-2.5 w-2.5" />
                {r.disease}
              </span>
            ))}
          </div>

          {/* Reasons */}
          <div className="space-y-0.5">
            {highRisks.map(r => (
              <p key={r.disease} className="text-[11px] opacity-80">
                <strong>{r.disease}:</strong> {r.reason}
              </p>
            ))}
          </div>

          {/* Tip */}
          <div className="mt-2 flex items-start gap-1.5 text-[11px] opacity-75">
            <Info className="h-3 w-3 shrink-0 mt-0.5" />
            <span>Mention any related symptoms early for faster guidance.</span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
