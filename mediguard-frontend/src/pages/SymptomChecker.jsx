import React, { useState, useEffect } from 'react';
import { Helmet } from 'react-helmet';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Loader2, Search, Thermometer, Activity, Baby, User,
  CheckCircle2, XCircle, HelpCircle, Wand2, ShieldCheck, Sparkles, Target,
  Trophy, Wind, Stethoscope, Brain, Eye, Droplets, Gauge, CircleDot,
  ChevronRight, ChevronLeft, SkipForward, Star, Flame,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { getAllSymptoms, diseases as diseaseDB } from '@/data/diseases';
import { getSymptoms, predictDisease, normalizeSymptoms, getClarifyQuestions } from '@/services/api';
import DisclaimerBanner from '@/components/DisclaimerBanner';

// ─── Static Data ─────────────────────────────────────────────────────────────

const CATEGORIES_MAP = {
  'Fever & Systemic': ['Fever', 'High fever', 'Prolonged fever', 'Sudden high fever', 'Mild fever', 'Chills', 'Sweating', 'Night sweats', 'Fatigue', 'Weakness', 'Weight loss', 'Swollen lymph nodes', 'Body aches'],
  'Respiratory': ['Cough', 'Chronic cough', 'Shortness of breath', 'Chest pain', 'Chest tightness', 'Runny nose', 'Sore throat', 'Nasal congestion', 'Coughing up blood', 'Wheezing', 'Hoarse voice'],
  'Gastrointestinal': ['Nausea', 'Vomiting', 'Diarrhea', 'Profuse watery diarrhea', 'Bloody or mucus-filled diarrhea', 'Abdominal pain', 'Lower abdominal pain', 'Constipation', 'Loss of appetite', 'Bloating', 'Heartburn', 'Jaundice'],
  'Pain & Neurological': ['Headache', 'Severe headache', 'Joint pain', 'Muscle aches', 'Back pain', 'Stiff neck', 'Confusion', 'Dizziness', 'Seizures', 'Numbness', 'Sensitivity to light', 'Jaw stiffness', 'Ear pain', 'Facial pain'],
  'Skin & Eyes': ['Rash', 'Itchy rash', 'Itchy skin', 'Ring-shaped rash', 'Blisters', 'Skin lesions', 'Skin sores', 'Pale skin', 'Red eyes', 'Yellow eyes', 'Eye discharge', 'Pus or discharge', 'Hair loss'],
  'Urinary & Reproductive': ['Frequent urination', 'Painful urination', 'Blood in urine', 'Pelvic pain', 'Vaginal discharge', 'Vaginal itching', 'Vaginal bleeding', 'Missed period', 'Pain during intercourse'],
  'Metabolic & Endocrine': ['Increased thirst', 'Slow-healing sores', 'Blurred vision', 'Fast heartbeat', 'Low blood pressure', 'Swollen feet', 'Dark urine', 'Weight gain', 'Heat intolerance', 'Cold intolerance'],
  'Other': ['Hearing loss', 'Difficulty swallowing', 'Visible worms in stool', 'Anal itching', 'White patches in mouth', 'Anxiety', 'Tremor'],
};

const CATEGORY_META = {
  'Fever & Systemic': { icon: Thermometer, accent: 'text-red-600', bg: 'bg-red-50 dark:bg-red-950/20', border: 'border-red-300 dark:border-red-900/60', ringColor: 'ring-red-400', comment: 'Start here — fever, chills, fatigue, sweats, or weakness.' },
  'Respiratory': { icon: Wind, accent: 'text-sky-600', bg: 'bg-sky-50 dark:bg-sky-950/20', border: 'border-sky-300 dark:border-sky-900/60', ringColor: 'ring-sky-400', comment: 'Cough, chest pain, wheezing, or shortness of breath.' },
  'Gastrointestinal': { icon: Stethoscope, accent: 'text-emerald-600', bg: 'bg-emerald-50 dark:bg-emerald-950/20', border: 'border-emerald-300 dark:border-emerald-900/60', ringColor: 'ring-emerald-400', comment: 'Nausea, vomiting, diarrhea, abdominal pain.' },
  'Pain & Neurological': { icon: Brain, accent: 'text-violet-600', bg: 'bg-violet-50 dark:bg-violet-950/20', border: 'border-violet-300 dark:border-violet-900/60', ringColor: 'ring-violet-400', comment: 'Headache, joint pain, confusion, dizziness, stiff neck.' },
  'Skin & Eyes': { icon: Eye, accent: 'text-amber-600', bg: 'bg-amber-50 dark:bg-amber-950/20', border: 'border-amber-300 dark:border-amber-900/60', ringColor: 'ring-amber-400', comment: 'Rash, blisters, red/yellow eyes, skin changes.' },
  'Urinary & Reproductive': { icon: Droplets, accent: 'text-pink-600', bg: 'bg-pink-50 dark:bg-pink-950/20', border: 'border-pink-300 dark:border-pink-900/60', ringColor: 'ring-pink-400', comment: 'Painful urination, pelvic pain, discharge, bleeding.' },
  'Metabolic & Endocrine': { icon: Gauge, accent: 'text-cyan-700', bg: 'bg-cyan-50 dark:bg-cyan-950/20', border: 'border-cyan-300 dark:border-cyan-900/60', ringColor: 'ring-cyan-400', comment: 'Thirst, blurred vision, swelling, heartbeat changes.' },
  'Other': { icon: CircleDot, accent: 'text-slate-600', bg: 'bg-slate-50 dark:bg-slate-900/40', border: 'border-slate-300 dark:border-slate-800', ringColor: 'ring-slate-400', comment: 'Hearing loss, difficulty swallowing, mouth changes, tremor.' },
};

const CATEGORIES = Object.keys(CATEGORIES_MAP);


// ─── Animation Variants ───────────────────────────────────────────────────────

const zoneVariants = {
  enter: (dir) => ({ x: dir > 0 ? '75%' : '-75%', opacity: 0, scale: 0.96 }),
  center: { x: 0, opacity: 1, scale: 1, transition: { type: 'spring', stiffness: 280, damping: 28 } },
  exit: (dir) => ({ x: dir > 0 ? '-45%' : '45%', opacity: 0, scale: 0.97, transition: { duration: 0.18 } }),
};

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.05 } },
  exit: { opacity: 0, transition: { duration: 0.15 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 14 },
  visible: { opacity: 1, y: 0 },
};

const tileVariants = {
  hidden: { opacity: 0, scale: 0.82, y: 8 },
  visible: (i) => ({ opacity: 1, scale: 1, y: 0, transition: { type: 'spring', stiffness: 380, damping: 24, delay: i * 0.03 } }),
};

// ─── Component ────────────────────────────────────────────────────────────────

const SymptomChecker = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  // Wizard steps: 1 = symptom zones, 2 = clarifying questions
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [normalizing, setNormalizing] = useState(false);

  // Zone navigation within step 1
  const [categoryStep, setCategoryStep] = useState(0);
  const [direction, setDirection] = useState(1);
  const [justCompleted, setJustCompleted] = useState(false);

  // Symptom state
  const [allSymptoms, setAllSymptoms] = useState(getAllSymptoms());
  const [selectedSymptoms, setSelectedSymptoms] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [freeText, setFreeText] = useState('');

  // Personal info
  const [formData, setFormData] = useState({
    duration: '', severity: '', gender: '', age: '',
    isPregnant: false, pregnancyWeeks: '', fatigueContext: false,
  });
  const [showPregnancyOption, setShowPregnancyOption] = useState(false);
  const [showPersonalInfo, setShowPersonalInfo] = useState(true);

  // Clarify state
  const [clarifyQuestions, setClarifyQuestions] = useState([]);
  const [clarifyAnswers, setClarifyAnswers] = useState({});

  useEffect(() => {
    getSymptoms()
      .then((res) => {
        if (Array.isArray(res.data.symptoms) && res.data.symptoms.length) {
          setAllSymptoms(res.data.symptoms);
        }
      })
      .catch(() => setAllSymptoms(getAllSymptoms()));
  }, []);

  useEffect(() => {
    if (formData.gender === 'female') {
      setShowPregnancyOption(true);
    } else {
      setShowPregnancyOption(false);
      setFormData(prev => ({ ...prev, isPregnant: false, pregnancyWeeks: '' }));
    }
  }, [formData.gender]);

  // ─── Zone helpers ──────────────────────────────────────────────────────────

  const currentCategory = CATEGORIES[categoryStep];
  const isLastZone = categoryStep === CATEGORIES.length - 1;
  const meta = CATEGORY_META[currentCategory] || {};
  const ZoneIcon = meta.icon || Activity;

  const selectedInCurrentZone = (CATEGORIES_MAP[currentCategory] || []).filter(
    s => allSymptoms.includes(s) && selectedSymptoms.includes(s)
  );

  const goNextZone = () => {
    if (selectedInCurrentZone.length > 0) {
      setJustCompleted(true);
      setTimeout(() => setJustCompleted(false), 900);
    }
    setDirection(1);
    setCategoryStep(prev => Math.min(CATEGORIES.length - 1, prev + 1));
  };

  const goPrevZone = () => {
    setDirection(-1);
    setCategoryStep(prev => Math.max(0, prev - 1));
  };

  const jumpToZone = (i) => {
    setDirection(i > categoryStep ? 1 : -1);
    setCategoryStep(i);
  };

  // ─── Handlers ─────────────────────────────────────────────────────────────

  const handleSymptomToggle = (symptom) => {
    setSelectedSymptoms(prev =>
      prev.includes(symptom) ? prev.filter(s => s !== symptom) : [...prev, symptom]
    );
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleNormalizeText = async () => {
    const text = freeText.trim();
    if (!text) return;
    setNormalizing(true);
    try {
      const res = await normalizeSymptoms(text);
      const matched = res.data.matched || [];
      if (matched.length === 0) {
        toast({ title: 'No symptoms recognised', description: 'Try different wording or select from the zones below.' });
      } else {
        const added = matched.filter(s => !selectedSymptoms.includes(s));
        if (added.length > 0) {
          setSelectedSymptoms(prev => [...prev, ...added]);
          toast({ title: `${added.length} symptom${added.length > 1 ? 's' : ''} added`, description: added.join(', ') });
        } else {
          toast({ title: 'Already selected', description: 'All matched symptoms are already in your list.' });
        }
        setFreeText('');
      }
    } catch {
      toast({ variant: 'destructive', title: 'Could not normalise text', description: 'Select symptoms from the zones below.' });
    } finally {
      setNormalizing(false);
    }
  };

  const handleFreeTextKeyDown = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); handleNormalizeText(); }
  };

  const generatePredictionsLocal = (symptomsToAnalyze) =>
    diseaseDB
      .map(disease => {
        let matchCount = 0;
        let confidenceBoost = 0;
        symptomsToAnalyze.forEach(symptom => {
          const s = symptom.toLowerCase();
          if (disease.symptoms.some(ds => ds.toLowerCase() === s)) matchCount++;
          if (disease.confidenceFactors?.includes(symptom)) confidenceBoost += 10;
        });
        let confidence = disease.symptoms.length > 0
          ? (matchCount / Math.min(disease.symptoms.length, 5)) * 100 * 0.6
          : 0;
        confidence += confidenceBoost;
        if (formData.severity === 'severe' && disease.severity === 'High') confidence += 15;
        if (formData.duration === '2+ weeks' && disease.chronic) confidence += 10;
        confidence = Math.min(Math.max(Math.round(confidence), 0), 98);
        return { ...disease, confidence, matchCount };
      })
      .filter(d => d.matchCount > 0 || d.confidence > 20)
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, 7);

  const handleInitialSubmit = async (e) => {
    e?.preventDefault();
    if (selectedSymptoms.length === 0) {
      toast({ variant: 'destructive', title: 'No symptoms selected', description: 'Select or describe at least one symptom.' });
      return;
    }
    setLoading(true);
    try {
      const res = await predictDisease(selectedSymptoms, {
        gender: formData.gender || null,
        is_pregnant: formData.isPregnant,
        pregnancy_weeks: formData.pregnancyWeeks ? Number(formData.pregnancyWeeks) : null,
        fatigue_context: formData.fatigueContext,
      });
      const apiPredictions = mapApiPredictions(res.data.predictions || [], selectedSymptoms);
      const normSymptoms = res.data.normalized_symptoms || selectedSymptoms;
      const topDiseases = (res.data.predictions || []).slice(0, 5).map(p => p.disease || p.name);

      const clarifyRes = await getClarifyQuestions(normSymptoms, topDiseases, []);
      if (clarifyRes.data.should_ask && (clarifyRes.data.questions || []).length > 0) {
        setClarifyQuestions(clarifyRes.data.questions);
        setClarifyAnswers({});
        setStep(2);
      } else {
        navigateToResults(res, apiPredictions, selectedSymptoms);
      }
    } catch {
      toast({ title: 'Backend unavailable', description: 'Using local symptom matching.' });
      const results = generatePredictionsLocal(selectedSymptoms);
      navigate('/prediction-results', { state: buildResultState(selectedSymptoms, results, null, null, null) });
    } finally {
      setLoading(false);
    }
  };

  const handleFinalSubmit = async () => {
    setLoading(true);
    const confirmedExtras = clarifyQuestions
      .filter(q => clarifyAnswers[q.symptom] === 'yes')
      .map(q => q.symptom);
    const finalSymptoms = [...new Set([...selectedSymptoms, ...confirmedExtras])];
    try {
      const res = await predictDisease(finalSymptoms, {
        gender: formData.gender || null,
        is_pregnant: formData.isPregnant,
        pregnancy_weeks: formData.pregnancyWeeks ? Number(formData.pregnancyWeeks) : null,
        fatigue_context: formData.fatigueContext,
      });
      const apiPredictions = mapApiPredictions(res.data.predictions || [], finalSymptoms);
      navigateToResults(res, apiPredictions, finalSymptoms);
    } catch {
      const results = generatePredictionsLocal(selectedSymptoms);
      navigate('/prediction-results', { state: buildResultState(selectedSymptoms, results, null, null, null) });
    } finally {
      setLoading(false);
    }
  };

  const navigateToResults = (res, apiPredictions, symptoms) => {
    navigate('/prediction-results', {
      state: buildResultState(symptoms, apiPredictions, res.data.disclaimer, res.data.pregnancy_note, res.data.normalized_symptoms, res.data.prediction_log_id, res.data.fatigue_note),
    });
  };

  const buildResultState = (symptoms, predictions, disclaimer, pregnancyNote, normSymptoms, predictionLogId, fatigueNote = null) => ({
    symptoms,
    normalizedSymptoms: normSymptoms || symptoms,
    duration: formData.duration || 'Not specified',
    severity: formData.severity || 'Not specified',
    gender: formData.gender || 'Not specified',
    age: formData.age || 'Not specified',
    isPregnant: formData.isPregnant,
    pregnancyWeeks: formData.pregnancyWeeks || 'Not specified',
    fatigueContext: formData.fatigueContext,
    predictions,
    disclaimer,
    pregnancyNote,
    fatigueNote,
    predictionLogId: predictionLogId || null,
  });

  const mapApiPredictions = (predictions, symptoms) =>
    predictions.map(item => ({
      ...item,
      id: item.id || item.slug || (item.disease || item.name || '').toLowerCase().replace(/\s+/g, '-'),
      name: item.name || item.disease,
      confidence: item.confidence ?? item.probability ?? 0,
      description: item.description || 'Disease information is available in the disease library.',
      symptoms: item.symptoms || symptoms,
      severity: item.severity || 'Medium',
      whenToSeeDoctorUrgency: item.severity === 'High' ? 'red' : 'yellow',
      whenToSeeDoctorText: 'Please consult a qualified healthcare professional for proper assessment.',
    }));

  // ─── Computed values ───────────────────────────────────────────────────────

  const filteredSymptoms = allSymptoms.filter(s => s.toLowerCase().includes(searchQuery.toLowerCase()));
  const categoryStats = CATEGORIES.map(cat => {
    const available = (CATEGORIES_MAP[cat] || []).filter(s => allSymptoms.includes(s));
    const selected = available.filter(s => selectedSymptoms.includes(s));
    return { category: cat, available, selected, count: selected.length };
  });
  const activeCategoryCount = categoryStats.filter(c => c.count > 0).length;
  const scanProgress = Math.min(100, selectedSymptoms.length * 16 + activeCategoryCount * 8 + (formData.duration ? 8 : 0) + (formData.severity ? 8 : 0));
  const scanRank = selectedSymptoms.length >= 6 ? 'Deep scan ready' : selectedSymptoms.length >= 3 ? 'Good signal' : selectedSymptoms.length >= 1 ? 'Signal acquired' : 'Awaiting input';

  // ─── Symptom Tile ──────────────────────────────────────────────────────────

  const SymptomTile = ({ symptom, index }) => {
    const selected = selectedSymptoms.includes(symptom);
    return (
      <motion.div
        custom={index}
        variants={tileVariants}
        whileHover={{ y: -4, scale: 1.04 }}
        whileTap={{ scale: 0.93 }}
        onClick={() => handleSymptomToggle(symptom)}
        className={`relative cursor-pointer select-none rounded-xl border-2 p-2.5 sm:p-3 min-h-[60px] sm:min-h-[68px] flex items-center gap-2 sm:gap-3 transition-colors ${
          selected
            ? `border-primary bg-primary/10 ring-2 ring-primary/30 shadow-md`
            : 'border-border/60 bg-background hover:border-primary/40 hover:bg-muted/30'
        }`}
      >
        <div className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 transition-all ${
          selected ? 'border-primary bg-primary' : 'border-muted-foreground/30'
        }`}>
          <AnimatePresence>
            {selected && (
              <motion.div
                key="check"
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                exit={{ scale: 0 }}
                transition={{ type: 'spring', stiffness: 600, damping: 22 }}
              >
                <CheckCircle2 className="h-3.5 w-3.5 text-primary-foreground" />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        <span className={`flex-1 text-xs sm:text-sm font-semibold leading-tight ${selected ? 'text-primary' : 'text-foreground'}`}>
          {symptom}
        </span>
        {selected && (
          <motion.div
            layoutId={`glow-${symptom}`}
            className="absolute inset-0 rounded-xl bg-primary/5 pointer-events-none"
          />
        )}
      </motion.div>
    );
  };

  // ─── Zone Mini-Map ─────────────────────────────────────────────────────────

  const ZoneMap = () => (
    <div className="flex items-center justify-center flex-wrap gap-1 py-3 px-2">
      {CATEGORIES.map((cat, i) => {
        const Icon = CATEGORY_META[cat]?.icon || Activity;
        const stat = categoryStats[i];
        const isActive = i === categoryStep;
        const hasSelection = stat.count > 0;
        return (
          <React.Fragment key={cat}>
            <motion.button
              type="button"
              onClick={() => jumpToZone(i)}
              whileHover={{ scale: 1.15 }}
              whileTap={{ scale: 0.88 }}
              title={cat}
              className="relative"
            >
              <div className={`w-9 h-9 rounded-full flex items-center justify-center border-2 transition-all duration-200 ${
                isActive
                  ? `${CATEGORY_META[cat]?.bg} ${CATEGORY_META[cat]?.border} scale-110 shadow-md`
                  : hasSelection
                    ? 'bg-primary/20 border-primary/60'
                    : i < categoryStep
                      ? 'bg-muted/60 border-muted-foreground/20'
                      : 'bg-background border-border/50'
              }`}>
                {hasSelection && !isActive
                  ? <motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ duration: 2.4, repeat: Infinity }}>
                      <Icon className="h-4 w-4 text-primary" />
                    </motion.div>
                  : <Icon className={`h-4 w-4 ${isActive ? (CATEGORY_META[cat]?.accent || 'text-primary') : 'text-muted-foreground/60'}`} />
                }
              </div>
              {hasSelection && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute -top-1 -right-1 w-4 h-4 bg-primary rounded-full flex items-center justify-center shadow"
                >
                  <span className="text-[8px] font-bold text-primary-foreground">{stat.count}</span>
                </motion.div>
              )}
            </motion.button>
            {i < CATEGORIES.length - 1 && (
              <div className={`h-0.5 w-4 rounded-full transition-all duration-300 ${i < categoryStep ? 'bg-primary/60' : 'bg-border/40'}`} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );

  // ─── Render ────────────────────────────────────────────────────────────────

  return (
    <>
      <Helmet>
        <title>Symptom Checker - MediGuard Bamenda</title>
        <meta name="description" content="AI-powered symptom checker for Bamenda health community." />
      </Helmet>

      {/* Zone-complete flash overlay */}
      <AnimatePresence>
        {justCompleted && (
          <>
            <motion.div
              key="flash"
              className="fixed inset-0 z-50 pointer-events-none"
              initial={{ opacity: 0.25 }}
              animate={{ opacity: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.7 }}
              style={{ background: 'hsl(var(--primary) / 0.12)' }}
            />
            <motion.div
              key="badge"
              className="fixed top-1/3 left-1/2 z-50 pointer-events-none -translate-x-1/2 -translate-y-1/2"
              initial={{ scale: 0, opacity: 1 }}
              animate={{ scale: [0, 1.15, 1], opacity: [1, 1, 0] }}
              transition={{ duration: 0.85, times: [0, 0.45, 1] }}
            >
              <div className="flex items-center gap-3 rounded-2xl bg-primary px-8 py-4 text-primary-foreground shadow-2xl">
                <Star className="h-6 w-6 fill-current" />
                <span className="text-xl font-bold">Zone Cleared!</span>
                <Star className="h-6 w-6 fill-current" />
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <div className="min-h-screen bg-[linear-gradient(180deg,hsl(var(--muted)/0.45),hsl(var(--background))_38%,hsl(var(--muted)/0.25))] py-8 sm:py-12">
        <div className="container mx-auto px-4 max-w-5xl">

          {/* ── Global Header ─────────────────────────────────────────────── */}
          <div className="mb-5 overflow-hidden rounded-2xl border bg-background shadow-sm">
            {/* Main title row */}
            <div className="flex items-center gap-3 p-4 sm:p-5">
              <motion.div
                animate={{ rotate: [0, -6, 6, 0], scale: [1, 1.06, 1] }}
                transition={{ duration: 3, repeat: Infinity, repeatDelay: 1.5 }}
                className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-primary/10"
              >
                <Thermometer className="h-6 w-6 text-primary" />
              </motion.div>
              <div className="flex-1 min-w-0">
                <h1 className="text-2xl font-bold text-foreground sm:text-3xl">Symptom Checker</h1>
                <p className="mt-0.5 text-sm text-muted-foreground leading-snug hidden sm:block">
                  Move through symptom zones, collect clues, then launch the diagnosis scan.
                </p>
              </div>
              <div className="flex items-center gap-2 flex-wrap justify-end shrink-0">
                <Badge className="gap-1 bg-primary/10 text-primary hover:bg-primary/10 text-xs">
                  <ShieldCheck className="h-3 w-3" />Guided
                </Badge>
                <motion.div key={scanRank} initial={{ opacity: 0, scale: 0.85 }} animate={{ opacity: 1, scale: 1 }}>
                  <Badge variant="outline" className="gap-1 text-xs">
                    <Flame className={`h-3 w-3 ${selectedSymptoms.length >= 3 ? 'text-orange-500' : 'text-muted-foreground'}`} />
                    {scanRank}
                  </Badge>
                </motion.div>
              </div>
            </div>

            {/* Scan charge bar — compact inline strip */}
            <div className="border-t bg-muted/30 px-4 py-2.5 flex items-center gap-3">
              <span className="text-xs font-semibold text-muted-foreground shrink-0">Scan charge</span>
              <div className="flex-1 h-2.5 overflow-hidden rounded-full bg-muted">
                <motion.div
                  className="h-full rounded-full bg-gradient-to-r from-primary to-primary/70"
                  initial={false}
                  animate={{ width: `${scanProgress}%` }}
                  transition={{ type: 'spring', stiffness: 80, damping: 18 }}
                />
              </div>
              <motion.span key={scanProgress} initial={{ scale: 1.3 }} animate={{ scale: 1 }}
                className="text-xs font-bold text-primary shrink-0">{scanProgress}%</motion.span>
              {selectedSymptoms.length > 0 && (
                <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}>
                  <Badge className="gap-1 bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300 text-xs shrink-0">
                    <Trophy className="h-3 w-3" />{selectedSymptoms.length}
                  </Badge>
                </motion.div>
              )}
            </div>
          </div>

          {/* ── Global Step Indicator ──────────────────────────────────────── */}
          <div className="flex items-center justify-center gap-4 mb-6">
            {['Symptom Zones', 'Follow-up Questions'].map((label, i) => {
              const idx = i + 1;
              const active = step === idx;
              const done = step > idx;
              return (
                <React.Fragment key={label}>
                  <div className="flex items-center gap-2">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-all ${done ? 'bg-primary border-primary text-primary-foreground' : active ? 'bg-primary/10 border-primary text-primary scale-110 shadow-sm' : 'bg-muted border-muted-foreground/30 text-muted-foreground'}`}>
                      {done ? <CheckCircle2 className="h-4 w-4" /> : idx}
                    </div>
                    <span className={`text-sm font-medium ${active ? 'text-primary' : done ? 'text-foreground' : 'text-muted-foreground'}`}>{label}</span>
                  </div>
                  {i < 1 && <div className={`flex-1 max-w-16 h-0.5 rounded-full ${step > 1 ? 'bg-primary' : 'bg-muted-foreground/20'}`} />}
                </React.Fragment>
              );
            })}
          </div>

          <DisclaimerBanner variant="warning" className="mb-6" />

          {/* ── Main Content ───────────────────────────────────────────────── */}
          <AnimatePresence mode="wait">

            {/* ════════════════ STEP 1: Symptom Zones ════════════════ */}
            {step === 1 && (
              <motion.div key="step1" variants={containerVariants} initial="hidden" animate="visible" exit="exit">
                <form onSubmit={handleInitialSubmit}>

                  {/* Personal Info (collapsible) */}
                  <motion.div variants={itemVariants} className="mb-5">
                    <button
                      type="button"
                      onClick={() => setShowPersonalInfo(v => !v)}
                      className="w-full flex items-center justify-between px-5 py-3 rounded-xl border bg-background hover:bg-muted/40 transition-colors text-left"
                    >
                      <span className="flex items-center gap-2 font-semibold text-sm">
                        <User className="h-4 w-4 text-primary" />
                        Personal Information (Optional — improves accuracy)
                      </span>
                      <motion.div animate={{ rotate: showPersonalInfo ? 90 : 0 }}>
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      </motion.div>
                    </button>

                    <AnimatePresence>
                      {showPersonalInfo && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.25 }}
                          className="overflow-hidden"
                        >
                          <Card className="rounded-t-none border-t-0 shadow-sm">
                            <CardContent className="pt-5">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                <div className="space-y-2">
                                  <Label className="font-medium text-sm">Gender</Label>
                                  <RadioGroup name="gender" value={formData.gender}
                                    onValueChange={v => setFormData(prev => ({ ...prev, gender: v }))}
                                    className="flex gap-4">
                                    {['male', 'female', 'other'].map(g => (
                                      <div key={g} className="flex items-center gap-2">
                                        <RadioGroupItem value={g} id={g} />
                                        <Label htmlFor={g} className="capitalize cursor-pointer">{g}</Label>
                                      </div>
                                    ))}
                                  </RadioGroup>
                                </div>
                                <div className="space-y-2">
                                  <Label htmlFor="age" className="font-medium text-sm">Age</Label>
                                  <Input id="age" name="age" type="number" min="0" max="120"
                                    value={formData.age} onChange={handleInputChange} placeholder="Your age" className="h-10" />
                                </div>

                                {showPregnancyOption && (
                                  <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-[1fr_160px] gap-3 p-4 bg-pink-50 dark:bg-pink-950/20 rounded-lg border border-pink-200 dark:border-pink-900/50">
                                    <div className="flex items-center gap-2">
                                      <Checkbox id="isPregnant" checked={formData.isPregnant}
                                        onCheckedChange={checked => setFormData(prev => ({ ...prev, isPregnant: checked, pregnancyWeeks: checked ? prev.pregnancyWeeks : '' }))} />
                                      <Label htmlFor="isPregnant" className="flex items-center gap-2 cursor-pointer font-medium">
                                        <Baby className="h-4 w-4 text-pink-500" />Currently pregnant
                                      </Label>
                                    </div>
                                    <Input name="pregnancyWeeks" type="number" min="1" max="42"
                                      value={formData.pregnancyWeeks} onChange={handleInputChange}
                                      disabled={!formData.isPregnant} placeholder="Weeks" className="h-10" />
                                  </div>
                                )}

                                <div className="md:col-span-2 p-3 rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-900/50 dark:bg-amber-950/20 flex items-start gap-3">
                                  <Checkbox id="fatigueContext" checked={formData.fatigueContext}
                                    onCheckedChange={checked => setFormData(prev => ({ ...prev, fatigueContext: checked }))} className="mt-0.5" />
                                  <Label htmlFor="fatigueContext" className="cursor-pointer text-sm">
                                    <span className="font-semibold flex items-center gap-1"><Brain className="h-3.5 w-3.5 text-amber-600" />Symptoms may relate to fatigue, poor sleep, stress, or heavy activity</span>
                                    <span className="text-muted-foreground block mt-0.5">MediGuard will note this context while still checking for warning signs.</span>
                                  </Label>
                                </div>

                                <div className="space-y-2">
                                  <Label htmlFor="duration" className="font-medium text-sm">Symptom Duration</Label>
                                  <select id="duration" name="duration" value={formData.duration} onChange={handleInputChange}
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                                    <option value="">Select…</option>
                                    <option value="1-3 days">1–3 days</option>
                                    <option value="3-7 days">3–7 days</option>
                                    <option value="1-2 weeks">1–2 weeks</option>
                                    <option value="2+ weeks">More than 2 weeks</option>
                                  </select>
                                </div>
                                <div className="space-y-2">
                                  <Label htmlFor="severity" className="font-medium text-sm">Overall Severity</Label>
                                  <select id="severity" name="severity" value={formData.severity} onChange={handleInputChange}
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                                    <option value="">Select…</option>
                                    <option value="mild">Mild — Annoying but manageable</option>
                                    <option value="moderate">Moderate — Affects daily activities</option>
                                    <option value="severe">Severe — Unable to function normally</option>
                                  </select>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>

                  {/* Free-text input */}
                  <motion.div variants={itemVariants} className="mb-5">
                    <Card className="border-primary/30 border shadow-sm">
                      <CardContent className="pt-4 pb-4">
                        <div className="flex items-center gap-2 mb-2">
                          <Wand2 className="h-4 w-4 text-primary" />
                          <span className="text-sm font-semibold">Describe symptoms in your own words</span>
                          <span className="text-xs text-muted-foreground">(handles typos & local names)</span>
                        </div>
                        <div className="flex gap-2">
                          <Input
                            value={freeText}
                            onChange={e => setFreeText(e.target.value)}
                            onKeyDown={handleFreeTextKeyDown}
                            placeholder='"feaver and body ache" or "diarrhoea with vomiting"'
                            className="h-10 flex-1"
                            disabled={normalizing}
                          />
                          <Button type="button" onClick={handleNormalizeText} disabled={normalizing || !freeText.trim()} className="h-10 px-5 shrink-0">
                            {normalizing ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Sparkles className="h-3.5 w-3.5 mr-1" />Add</>}
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>

                  {/* Search input */}
                  <motion.div variants={itemVariants} className="mb-5 relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                    <Input
                      type="text"
                      placeholder="Search all symptoms…"
                      value={searchQuery}
                      onChange={e => setSearchQuery(e.target.value)}
                      className="pl-12 h-11 bg-background shadow-sm"
                    />
                    {searchQuery && (
                      <button type="button" onClick={() => setSearchQuery('')}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                        <XCircle className="h-4 w-4" />
                      </button>
                    )}
                  </motion.div>

                  {/* ── Search results OR Zone slider ── */}
                  <AnimatePresence mode="wait">
                    {searchQuery.length > 0 ? (
                      <motion.div key="search" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                        <Card className="mb-6 border-2 border-primary/20 shadow-md">
                          <CardHeader className="pb-3 border-b">
                            <CardTitle className="text-base">Search Results — {filteredSymptoms.length} found</CardTitle>
                          </CardHeader>
                          <CardContent className="pt-4">
                            <motion.div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3" variants={containerVariants} initial="hidden" animate="visible">
                              {filteredSymptoms.map((symptom, i) => (
                                <SymptomTile key={symptom} symptom={symptom} index={i} />
                              ))}
                            </motion.div>
                            {filteredSymptoms.length === 0 && (
                              <p className="text-center py-8 text-muted-foreground">No symptoms found. Try the text input above.</p>
                            )}
                          </CardContent>
                        </Card>
                      </motion.div>
                    ) : (
                      <motion.div key="zones" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                        {/* Zone Mini-Map */}
                        <div className="mb-4 rounded-xl border bg-background shadow-sm overflow-hidden">
                          <div className="px-4 pt-3 pb-1 flex items-center justify-between">
                            <span className="text-sm font-bold text-foreground">
                              Zone {categoryStep + 1} of {CATEGORIES.length}
                            </span>
                            <span className="text-xs text-muted-foreground">Tap a zone to jump</span>
                          </div>
                          <ZoneMap />
                        </div>

                        {/* Zone Slider */}
                        <div className="relative overflow-hidden rounded-2xl border-2 shadow-lg" style={{ borderColor: `hsl(var(--border))` }}>
                          <AnimatePresence mode="wait" custom={direction}>
                            <motion.div
                              key={categoryStep}
                              custom={direction}
                              variants={zoneVariants}
                              initial="enter"
                              animate="center"
                              exit="exit"
                            >
                              {/* Zone Header */}
                              <div className={`${meta.bg || 'bg-muted/30'} border-b ${meta.border || 'border-border'} p-4 sm:p-5`}>
                                <div className="flex items-center justify-between gap-3">
                                  <div className="flex items-center gap-3">
                                    <motion.div
                                      initial={{ rotate: -20, scale: 0.7 }}
                                      animate={{ rotate: 0, scale: 1 }}
                                      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                                      className={`flex h-11 w-11 sm:h-14 sm:w-14 shrink-0 items-center justify-center rounded-xl sm:rounded-2xl border-2 ${meta.border || 'border-border'} ${meta.bg || 'bg-muted/30'} shadow-sm`}
                                    >
                                      <ZoneIcon className={`h-5 w-5 sm:h-7 sm:w-7 ${meta.accent || 'text-primary'}`} />
                                    </motion.div>
                                    <div>
                                      <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                                        <Badge variant="outline" className="text-xs font-bold bg-background/80">
                                          ZONE {categoryStep + 1}
                                        </Badge>
                                        {selectedInCurrentZone.length > 0 && (
                                          <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}>
                                            <Badge className="text-xs bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">
                                              <Star className="h-3 w-3 mr-1 fill-current" />{selectedInCurrentZone.length} selected
                                            </Badge>
                                          </motion.div>
                                        )}
                                      </div>
                                      <h2 className={`text-base sm:text-xl font-bold ${meta.accent || 'text-foreground'}`}>{currentCategory}</h2>
                                      <p className="text-xs sm:text-sm text-muted-foreground leading-snug hidden sm:block">{meta.comment}</p>
                                    </div>
                                  </div>
                                </div>
                              </div>

                              {/* Zone Symptom Grid */}
                              <div className="p-4 sm:p-5 bg-background">
                                <motion.div
                                  className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3"
                                  variants={containerVariants}
                                  initial="hidden"
                                  animate="visible"
                                >
                                  {(CATEGORIES_MAP[currentCategory] || []).map((symptom, i) => {
                                    if (!allSymptoms.includes(symptom)) return null;
                                    return <SymptomTile key={symptom} symptom={symptom} index={i} />;
                                  })}
                                </motion.div>

                                {(CATEGORIES_MAP[currentCategory] || []).filter(s => allSymptoms.includes(s)).length === 0 && (
                                  <p className="text-center py-8 text-muted-foreground">No symptoms available in this zone.</p>
                                )}
                              </div>

                              {/* Zone Navigation */}
                              <div className={`flex items-center justify-between gap-2 px-4 sm:px-5 py-3 border-t ${meta.bg || 'bg-muted/20'}`}>
                                <Button
                                  type="button"
                                  variant="outline"
                                  size="sm"
                                  className="gap-1.5 h-10 px-3 sm:px-4"
                                  onClick={goPrevZone}
                                  disabled={categoryStep === 0}
                                >
                                  <ChevronLeft className="h-4 w-4" /><span className="hidden sm:inline">Back</span>
                                </Button>

                                <div className="flex items-center gap-1">
                                  {CATEGORIES.map((_, i) => (
                                    <div key={i} className={`h-1.5 rounded-full transition-all duration-300 ${
                                      i === categoryStep ? 'w-5 bg-primary' :
                                      categoryStats[i].count > 0 ? 'w-1.5 bg-primary/50' :
                                      'w-1.5 bg-muted-foreground/25'
                                    }`} />
                                  ))}
                                </div>

                                {isLastZone ? (
                                  <motion.div
                                    animate={selectedSymptoms.length > 0 ? { scale: [1, 1.04, 1] } : {}}
                                    transition={{ duration: 1.6, repeat: Infinity }}
                                  >
                                    <Button
                                      type="submit"
                                      size="sm"
                                      disabled={loading || selectedSymptoms.length === 0}
                                      className="gap-1.5 h-10 px-3 sm:px-4 bg-gradient-to-r from-primary to-primary/80 shadow-lg"
                                    >
                                      {loading
                                        ? <><Loader2 className="h-4 w-4 animate-spin" /><span className="hidden sm:inline">Scanning…</span></>
                                        : <><Sparkles className="h-4 w-4" /><span className="hidden sm:inline">Launch Scan</span><span className="sm:hidden">Scan</span></>
                                      }
                                    </Button>
                                  </motion.div>
                                ) : (
                                  <Button type="button" size="sm" onClick={goNextZone} className="gap-1.5 h-10 px-3 sm:px-4">
                                    {selectedInCurrentZone.length > 0 ? (
                                      <><Star className="h-3.5 w-3.5 fill-current" /><span className="hidden sm:inline">Next Zone</span><span className="sm:hidden">Next</span><ChevronRight className="h-4 w-4" /></>
                                    ) : (
                                      <><SkipForward className="h-3.5 w-3.5" /><span className="hidden sm:inline">Skip</span><ChevronRight className="h-4 w-4" /></>
                                    )}
                                  </Button>
                                )}
                              </div>
                            </motion.div>
                          </AnimatePresence>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Sticky selected bar */}
                  <AnimatePresence>
                    {selectedSymptoms.length > 0 && (
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 20 }}
                        className="sticky bottom-4 z-20 mt-6"
                      >
                        <Card className="border-primary/50 bg-background/95 backdrop-blur shadow-2xl">
                          <div className="p-3 px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
                            <div className="flex-1 overflow-x-auto whitespace-nowrap flex items-center gap-2 py-1">
                              <span className="text-sm font-semibold shrink-0 flex items-center gap-1.5">
                                <Target className="h-4 w-4 text-primary" />
                                {selectedSymptoms.length} clue{selectedSymptoms.length !== 1 ? 's' : ''}:
                              </span>
                              {selectedSymptoms.map(symptom => (
                                <motion.span
                                  key={symptom}
                                  initial={{ scale: 0 }}
                                  animate={{ scale: 1 }}
                                  exit={{ scale: 0 }}
                                  className="inline-flex items-center px-3 py-1 bg-primary text-primary-foreground rounded-full text-xs font-medium cursor-pointer hover:bg-destructive transition-colors shrink-0"
                                  onClick={() => handleSymptomToggle(symptom)}
                                >
                                  {symptom} <XCircle className="ml-1.5 h-3 w-3 opacity-70" />
                                </motion.span>
                              ))}
                            </div>
                            {isLastZone && (
                              <Button type="submit" size="sm" disabled={loading} className="shrink-0 gap-1.5">
                                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                                {loading ? 'Scanning…' : 'Launch Scan'}
                              </Button>
                            )}
                          </div>
                        </Card>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Floating launch button (always available once symptoms selected, even mid-zones) */}
                  {!isLastZone && selectedSymptoms.length >= 2 && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="mt-6 flex justify-center"
                    >
                      <Button type="submit" size="lg" disabled={loading}
                        className="gap-2 h-12 px-10 text-base font-bold shadow-xl bg-gradient-to-r from-primary to-primary/80">
                        {loading
                          ? <><Loader2 className="h-5 w-5 animate-spin" />Analyzing…</>
                          : <><Sparkles className="h-5 w-5" />Launch Diagnosis Scan</>
                        }
                      </Button>
                    </motion.div>
                  )}

                </form>
              </motion.div>
            )}

            {/* ════════════════ STEP 2: Clarifying Questions ════════════════ */}
            {step === 2 && (
              <motion.div key="step2" variants={containerVariants} initial="hidden" animate="visible" exit="exit">
                <motion.div variants={itemVariants}>
                  <Card className="mb-6 shadow-md border-t-4 border-t-primary overflow-hidden">
                    <CardHeader className="bg-primary/5">
                      <CardTitle className="flex items-center gap-2">
                        <HelpCircle className="h-5 w-5 text-primary" />
                        A few follow-up questions
                      </CardTitle>
                      <CardDescription>
                        Your symptoms could match several conditions. These yes/no questions help the model narrow it down.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="pt-5 space-y-4">
                      {clarifyQuestions.map((q, i) => (
                        <motion.div
                          key={q.symptom}
                          variants={itemVariants}
                          whileHover={{ scale: 1.005 }}
                          className={`p-4 rounded-xl border-2 transition-all duration-200 ${
                            clarifyAnswers[q.symptom] === 'yes'
                              ? 'border-green-400 bg-green-50 dark:bg-green-950/20 shadow-sm'
                              : clarifyAnswers[q.symptom] === 'no'
                                ? 'border-muted bg-muted/30'
                                : 'border-border bg-background'
                          }`}
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                              <p className="text-xs text-muted-foreground mb-1 font-medium">
                                Question {i + 1} of {clarifyQuestions.length}
                              </p>
                              <p className="font-semibold text-foreground">{q.question}</p>
                              {q.helps_distinguish?.length > 0 && (
                                <p className="text-xs text-muted-foreground mt-1">
                                  Helps distinguish: {q.helps_distinguish.slice(0, 3).join(', ')}
                                  {q.helps_distinguish.length > 3 && '…'}
                                </p>
                              )}
                            </div>
                            <div className="flex gap-2 shrink-0">
                              <motion.div whileTap={{ scale: 0.9 }}>
                                <Button type="button" size="sm"
                                  variant={clarifyAnswers[q.symptom] === 'yes' ? 'default' : 'outline'}
                                  className={`gap-1 ${clarifyAnswers[q.symptom] === 'yes' ? 'bg-green-600 hover:bg-green-700 text-white border-green-600' : ''}`}
                                  onClick={() => setClarifyAnswers(prev => ({ ...prev, [q.symptom]: prev[q.symptom] === 'yes' ? undefined : 'yes' }))}>
                                  <CheckCircle2 className="h-4 w-4" />Yes
                                </Button>
                              </motion.div>
                              <motion.div whileTap={{ scale: 0.9 }}>
                                <Button type="button" size="sm"
                                  variant={clarifyAnswers[q.symptom] === 'no' ? 'secondary' : 'outline'}
                                  className="gap-1"
                                  onClick={() => setClarifyAnswers(prev => ({ ...prev, [q.symptom]: prev[q.symptom] === 'no' ? undefined : 'no' }))}>
                                  <XCircle className="h-4 w-4" />No
                                </Button>
                              </motion.div>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </CardContent>
                  </Card>
                </motion.div>

                <motion.div variants={itemVariants} className="flex flex-col sm:flex-row gap-4 justify-center pb-12">
                  <Button type="button" variant="outline" size="lg" className="h-12 px-8 gap-2"
                    onClick={() => setStep(1)}>
                    <ChevronLeft className="h-4 w-4" />Back to Zones
                  </Button>
                  <motion.div
                    animate={{ scale: [1, 1.03, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <Button type="button" size="lg" disabled={loading} className="h-12 px-12 font-bold shadow-xl gap-2"
                      onClick={handleFinalSubmit}>
                      {loading
                        ? <><Loader2 className="mr-2 h-5 w-5 animate-spin" />Getting results…</>
                        : <><Sparkles className="h-5 w-5" />Get Final Diagnosis</>
                      }
                    </Button>
                  </motion.div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>

        </div>
      </div>
    </>
  );
};

export default SymptomChecker;
