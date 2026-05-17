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
import { AlertCircle, Loader2, Search, Thermometer, Clock, Activity, Baby, User, Info, CheckCircle2, XCircle, HelpCircle, Wand2, ShieldCheck, Sparkles, Zap, Target, Trophy, HeartPulse, Wind, Stethoscope, Brain, Eye, Droplets, Gauge, CircleDot } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { getAllSymptoms, diseases as diseaseDB } from '@/data/diseases';
import { useAuth } from '@/components/AuthContext';
import { getSymptoms, predictDisease, normalizeSymptoms, getClarifyQuestions } from '@/services/api';
import DisclaimerBanner from '@/components/DisclaimerBanner';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08 } },
  exit: { opacity: 0, transition: { duration: 0.2 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0 },
};

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
  'Fever & Systemic': {
    icon: Thermometer,
    accent: 'text-red-600',
    bg: 'bg-red-50 dark:bg-red-950/20',
    border: 'border-red-200 dark:border-red-900/50',
    comment: 'Start here if the whole body feels off: fever, chills, tiredness, sweats, or weakness.',
  },
  Respiratory: {
    icon: Wind,
    accent: 'text-sky-600',
    bg: 'bg-sky-50 dark:bg-sky-950/20',
    border: 'border-sky-200 dark:border-sky-900/50',
    comment: 'Breathing clues matter. Cough, chest pain, wheezing, or shortness of breath can change urgency.',
  },
  Gastrointestinal: {
    icon: Stethoscope,
    accent: 'text-emerald-600',
    bg: 'bg-emerald-50 dark:bg-emerald-950/20',
    border: 'border-emerald-200 dark:border-emerald-900/50',
    comment: 'Gut symptoms often need hydration checks, especially vomiting or diarrhea.',
  },
  'Pain & Neurological': {
    icon: Brain,
    accent: 'text-violet-600',
    bg: 'bg-violet-50 dark:bg-violet-950/20',
    border: 'border-violet-200 dark:border-violet-900/50',
    comment: 'Pain pattern, headache severity, confusion, dizziness, and neck stiffness are important signals.',
  },
  'Skin & Eyes': {
    icon: Eye,
    accent: 'text-amber-600',
    bg: 'bg-amber-50 dark:bg-amber-950/20',
    border: 'border-amber-200 dark:border-amber-900/50',
    comment: 'Rashes, blisters, red eyes, pale skin, or yellow eyes help separate infections and chronic conditions.',
  },
  'Urinary & Reproductive': {
    icon: Droplets,
    accent: 'text-pink-600',
    bg: 'bg-pink-50 dark:bg-pink-950/20',
    border: 'border-pink-200 dark:border-pink-900/50',
    comment: 'Urine pain, pelvic pain, bleeding, or discharge should be answered carefully, especially in pregnancy.',
  },
  'Metabolic & Endocrine': {
    icon: Gauge,
    accent: 'text-cyan-700',
    bg: 'bg-cyan-50 dark:bg-cyan-950/20',
    border: 'border-cyan-200 dark:border-cyan-900/50',
    comment: 'Longer-term signals like thirst, blurred vision, swelling, and heartbeat changes can be subtle but useful.',
  },
  Other: {
    icon: CircleDot,
    accent: 'text-slate-600',
    bg: 'bg-slate-50 dark:bg-slate-900/40',
    border: 'border-slate-200 dark:border-slate-800',
    comment: 'Small clues can still matter. Add anything unusual, even if it feels unrelated.',
  },
};

const checkerTips = [
  'Pick the symptoms you actually feel today. More is not always better.',
  'Duration and severity sharpen the scan.',
  'For pregnancy, fever, bleeding, severe pain, or reduced fetal movement should be treated as urgent.',
  'You can type natural text first, then fine-tune the selected tiles.',
];

const SymptomChecker = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useAuth();

  // Step: 1 = symptom selection, 2 = clarifying questions
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [normalizing, setNormalizing] = useState(false);

  // Symptom selection state
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

  // Clarify state
  const [clarifyQuestions, setClarifyQuestions] = useState([]);
  const [clarifyAnswers, setClarifyAnswers] = useState({}); // symptom -> 'yes' | 'no'
  const [initialResult, setInitialResult] = useState(null); // saved from first predict call
  const [normalizedSymptoms, setNormalizedSymptoms] = useState([]);

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
        toast({ title: 'No symptoms recognised', description: 'Try using different wording or select from the list below.' });
      } else {
        const added = matched.filter(s => !selectedSymptoms.includes(s));
        if (added.length > 0) {
          setSelectedSymptoms(prev => [...prev, ...added]);
          toast({ title: `Added ${added.length} symptom${added.length > 1 ? 's' : ''}`, description: added.join(', ') });
        } else {
          toast({ title: 'Already selected', description: 'All matched symptoms are already in your list.' });
        }
        setFreeText('');
      }
    } catch {
      toast({ variant: 'destructive', title: 'Could not normalise text', description: 'Please select symptoms from the list below.' });
    } finally {
      setNormalizing(false);
    }
  };

  const handleFreeTextKeyDown = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); handleNormalizeText(); }
  };

  // Local fallback predictor (unchanged from original)
  const generatePredictionsLocal = (symptomsToAnalyze) => {
    return diseaseDB
      .map(disease => {
        let matchCount = 0;
        let confidenceBoost = 0;
        symptomsToAnalyze.forEach(symptom => {
          const s = symptom.toLowerCase();
          if (disease.symptoms.some(ds => ds.toLowerCase() === s)) { matchCount++; }
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
  };

  // Step 1 submit: run initial prediction + check if clarification needed
  const handleInitialSubmit = async (e) => {
    e.preventDefault();
    if (selectedSymptoms.length === 0) {
      toast({ variant: 'destructive', title: 'No symptoms selected', description: 'Please select or describe at least one symptom.' });
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

      setInitialResult({ res, apiPredictions, normSymptoms });
      setNormalizedSymptoms(normSymptoms);

      // Ask backend if clarification is needed
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
      navigate('/prediction-results', {
        state: buildResultState(selectedSymptoms, results, null, null, null),
      });
    } finally {
      setLoading(false);
    }
  };

  // Step 2 submit: add confirmed "yes" answers, run final prediction
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
      const results = generatePredictionsLocal(finalSymptoms);
      navigate('/prediction-results', {
        state: buildResultState(finalSymptoms, results, null, null, null),
      });
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

  const filteredSymptoms = allSymptoms.filter(s =>
    s.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // ─── Render ──────────────────────────────────────────────────────────────────
  const categoryStats = Object.entries(CATEGORIES_MAP).map(([category, symptoms]) => {
    const available = symptoms.filter(symptom => allSymptoms.includes(symptom));
    const selected = available.filter(symptom => selectedSymptoms.includes(symptom));
    return { category, available, selected, count: selected.length };
  });
  const activeCategoryCount = categoryStats.filter(item => item.count > 0).length;
  const scanProgress = Math.min(100, selectedSymptoms.length * 16 + activeCategoryCount * 8 + (formData.duration ? 8 : 0) + (formData.severity ? 8 : 0));
  const tipIndex = Math.min(checkerTips.length - 1, Math.floor(selectedSymptoms.length / 2));
  const scanRank = selectedSymptoms.length >= 6 ? 'Deep scan ready' : selectedSymptoms.length >= 3 ? 'Good signal' : selectedSymptoms.length >= 1 ? 'Signal acquired' : 'Awaiting symptoms';
  const liveMessage = loading
    ? 'Running model scan... hold steady.'
    : selectedSymptoms.length >= 5
      ? 'Great coverage. You have enough clues for a stronger check.'
      : selectedSymptoms.length >= 2
        ? 'Nice. Add duration, severity, or one more symptom if there is one.'
        : selectedSymptoms.length === 1
          ? 'One clue found. Add related symptoms so the model has context.'
          : 'Select symptoms or type them above to begin the scan.';

  const renderSymptomTile = (symptom, idPrefix = 'symptom') => {
    const selected = selectedSymptoms.includes(symptom);
    return (
      <motion.div
        key={symptom}
        whileHover={{ y: -2, scale: 1.01 }}
        whileTap={{ scale: 0.98 }}
        animate={selected ? { boxShadow: '0 10px 24px rgba(14, 165, 164, 0.16)' } : { boxShadow: '0 0 0 rgba(0,0,0,0)' }}
        className={`relative flex min-h-[56px] items-center gap-3 rounded-lg border p-3 transition-all ${
          selected
            ? 'border-primary bg-primary/10 text-primary'
            : 'border-border bg-background hover:border-primary/40 hover:bg-muted/40'
        }`}
      >
        <Checkbox id={`${idPrefix}-${symptom}`} checked={selected} onCheckedChange={() => handleSymptomToggle(symptom)} className="h-5 w-5" />
        <Label htmlFor={`${idPrefix}-${symptom}`} className="flex-1 cursor-pointer text-sm font-semibold leading-tight">
          {symptom}
        </Label>
        {selected && (
          <motion.span initial={{ scale: 0 }} animate={{ scale: 1 }} className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground">
            <CheckCircle2 className="h-3.5 w-3.5" />
          </motion.span>
        )}
      </motion.div>
    );
  };

  return (
    <>
      <Helmet>
        <title>Symptom Checker - MediGuard Bamenda</title>
        <meta name="description" content="Check your symptoms with our AI-powered symptom checker." />
      </Helmet>

      <div className="min-h-screen bg-[linear-gradient(180deg,hsl(var(--muted)/0.45),hsl(var(--background))_38%,hsl(var(--muted)/0.25))] py-8 sm:py-12">
        <div className="container mx-auto px-4 max-w-5xl">

          {/* Header */}
          <div className="mb-8 overflow-hidden rounded-xl border bg-background shadow-sm">
            <div className="grid gap-0 lg:grid-cols-[1fr_320px]">
              <div className="p-5 sm:p-7">
                <div className="mb-4 flex flex-wrap items-center gap-2">
                  <Badge className="gap-1 bg-primary/10 text-primary hover:bg-primary/10">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    Guided health scan
                  </Badge>
                  <Badge variant="outline" className="gap-1">
                    <Zap className="h-3.5 w-3.5 text-amber-500" />
                    {scanRank}
                  </Badge>
                </div>
                <div className="flex items-start gap-4">
                  <motion.div
                    animate={{ rotate: [0, -5, 5, 0], scale: [1, 1.04, 1] }}
                    transition={{ duration: 2.6, repeat: Infinity, repeatDelay: 1.2 }}
                    className="hidden h-16 w-16 items-center justify-center rounded-full bg-primary/10 sm:flex"
                  >
                    <Thermometer className="h-8 w-8 text-primary" />
                  </motion.div>
                  <div>
                    <h1 className="text-3xl font-bold text-foreground sm:text-4xl">Symptom Checker</h1>
                    <p className="mt-3 max-w-2xl text-base text-muted-foreground sm:text-lg">
                      Move through the symptom zones, collect the clues that match how you feel, then run the diagnosis scan.
                    </p>
                  </div>
                </div>
              </div>
              <div className="border-t bg-muted/30 p-5 lg:border-l lg:border-t-0">
                <div className="mb-3 flex items-center justify-between">
                  <span className="text-sm font-semibold text-muted-foreground">Scan charge</span>
                  <span className="text-sm font-bold text-primary">{scanProgress}%</span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-muted">
                  <motion.div
                    className="h-full rounded-full bg-primary"
                    initial={false}
                    animate={{ width: `${scanProgress}%` }}
                    transition={{ type: 'spring', stiffness: 90, damping: 18 }}
                  />
                </div>
                <div className="mt-4 rounded-lg border bg-background p-3">
                  <div className="mb-1 flex items-center gap-2 text-sm font-semibold">
                    <Sparkles className="h-4 w-4 text-primary" />
                    Live guide
                  </div>
                  <AnimatePresence mode="wait">
                    <motion.p
                      key={liveMessage}
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -6 }}
                      className="text-sm text-muted-foreground"
                    >
                      {liveMessage}
                    </motion.p>
                  </AnimatePresence>
                </div>
              </div>
            </div>
          </div>

          {/* Step indicator */}
          <div className="flex items-center justify-center gap-4 mb-8">
            {['Select Symptoms', 'Follow-up Questions'].map((label, i) => {
              const idx = i + 1;
              const active = step === idx;
              const done = step > idx;
              return (
                <React.Fragment key={label}>
                  <div className="flex items-center gap-2">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-colors ${done ? 'bg-primary border-primary text-primary-foreground' : active ? 'bg-primary/10 border-primary text-primary' : 'bg-muted border-muted-foreground/30 text-muted-foreground'}`}>
                      {done ? <CheckCircle2 className="h-4 w-4" /> : idx}
                    </div>
                    <span className={`text-sm font-medium ${active ? 'text-primary' : done ? 'text-foreground' : 'text-muted-foreground'}`}>{label}</span>
                  </div>
                  {i < 1 && <div className={`flex-1 max-w-16 h-0.5 ${step > 1 ? 'bg-primary' : 'bg-muted-foreground/20'}`} />}
                </React.Fragment>
              );
            })}
          </div>

          <DisclaimerBanner variant="warning" className="mb-6" />

          <div className="mb-6 grid gap-3 sm:grid-cols-3">
            <motion.div whileHover={{ y: -2 }} className="rounded-lg border bg-background p-4 shadow-sm">
              <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
                <Trophy className="h-4 w-4 text-amber-500" />
                Clues captured
              </div>
              <div className="text-3xl font-bold text-foreground">{selectedSymptoms.length}</div>
              <p className="mt-1 text-xs text-muted-foreground">Select only what you truly feel.</p>
            </motion.div>
            <motion.div whileHover={{ y: -2 }} className="rounded-lg border bg-background p-4 shadow-sm">
              <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
                <HeartPulse className="h-4 w-4 text-primary" />
                Zones active
              </div>
              <div className="text-3xl font-bold text-foreground">{activeCategoryCount}</div>
              <p className="mt-1 text-xs text-muted-foreground">Spread across symptom sections.</p>
            </motion.div>
            <motion.div whileHover={{ y: -2 }} className="rounded-lg border bg-background p-4 shadow-sm">
              <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
                <Info className="h-4 w-4 text-sky-600" />
                Side note
              </div>
              <AnimatePresence mode="wait">
                <motion.p
                  key={tipIndex}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  className="text-sm text-muted-foreground"
                >
                  {checkerTips[tipIndex]}
                </motion.p>
              </AnimatePresence>
            </motion.div>
          </div>

          <AnimatePresence mode="wait">
            {/* ── STEP 1: Symptom Selection ─────────────────────────────────── */}
            {step === 1 && (
              <motion.div key="step1" variants={containerVariants} initial="hidden" animate="visible" exit="exit">
                <form onSubmit={handleInitialSubmit}>

                  {/* Personal Information */}
                  <motion.div variants={itemVariants}>
                    <Card className="mb-6 shadow-md border-t-4 border-t-primary">
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <User className="h-5 w-5 text-primary" />
                          Personal Information (Optional)
                        </CardTitle>
                        <CardDescription>Helps us give more accurate results</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div className="space-y-3">
                            <Label className="font-medium flex items-center gap-2">
                              <User className="h-4 w-4 text-muted-foreground" /> Gender
                            </Label>
                            <RadioGroup
                              name="gender"
                              value={formData.gender}
                              onValueChange={value => setFormData(prev => ({ ...prev, gender: value }))}
                              className="flex space-x-4"
                            >
                              {['male', 'female', 'other'].map(g => (
                                <div key={g} className="flex items-center space-x-2">
                                  <RadioGroupItem value={g} id={g} />
                                  <Label htmlFor={g} className="capitalize">{g}</Label>
                                </div>
                              ))}
                            </RadioGroup>
                          </div>

                          <div className="space-y-2">
                            <Label htmlFor="age" className="font-medium flex items-center gap-2">
                              <Clock className="h-4 w-4 text-muted-foreground" /> Age
                            </Label>
                            <Input id="age" name="age" type="number" min="0" max="120"
                              value={formData.age} onChange={handleInputChange} placeholder="Enter your age" className="h-11" />
                          </div>

                          {showPregnancyOption && (
                            <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-[1fr_180px] gap-4 p-4 bg-primary/5 rounded-lg border border-primary/20">
                              <div className="flex items-center space-x-2">
                                <Checkbox id="isPregnant" checked={formData.isPregnant}
                                  onCheckedChange={checked => setFormData(prev => ({ ...prev, isPregnant: checked, pregnancyWeeks: checked ? prev.pregnancyWeeks : '' }))} />
                                <Label htmlFor="isPregnant" className="flex items-center gap-2 cursor-pointer">
                                  <Baby className="h-4 w-4 text-primary" />
                                  <span className="font-medium">I am currently pregnant</span>
                                </Label>
                              </div>
                              <Input name="pregnancyWeeks" type="number" min="1" max="42"
                                value={formData.pregnancyWeeks} onChange={handleInputChange}
                                disabled={!formData.isPregnant} placeholder="Weeks" className="h-10" />
                              <p className="sm:col-span-2 text-sm text-muted-foreground">
                                Pregnancy can change symptom urgency. MediGuard will flag warning signs and recommend antenatal care when needed.
                              </p>
                            </div>
                          )}

                          <div className="md:col-span-2 rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-900/50 dark:bg-amber-950/20">
                            <div className="flex items-start gap-3">
                              <Checkbox
                                id="fatigueContext"
                                checked={formData.fatigueContext}
                                onCheckedChange={checked => setFormData(prev => ({ ...prev, fatigueContext: checked }))}
                                className="mt-1"
                              />
                              <div>
                                <Label htmlFor="fatigueContext" className="flex cursor-pointer items-center gap-2 font-semibold">
                                  <Brain className="h-4 w-4 text-amber-600" />
                                  Symptoms may be related to fatigue, poor sleep, stress, dehydration, or heavy activity
                                </Label>
                                <p className="mt-1 text-sm text-muted-foreground">
                                  MediGuard will keep this in mind and remind you that fatigue can worsen symptoms, while still checking for warning signs.
                                </p>
                              </div>
                            </div>
                          </div>

                          <div className="space-y-2">
                            <Label htmlFor="duration" className="font-medium flex items-center gap-2">
                              <Clock className="h-4 w-4 text-muted-foreground" /> Symptom Duration
                            </Label>
                            <select id="duration" name="duration" value={formData.duration} onChange={handleInputChange}
                              className="flex h-11 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring shadow-sm">
                              <option value="">Select duration...</option>
                              <option value="1-3 days">1 to 3 days</option>
                              <option value="3-7 days">3 to 7 days</option>
                              <option value="1-2 weeks">1 to 2 weeks</option>
                              <option value="2+ weeks">More than 2 weeks</option>
                            </select>
                          </div>

                          <div className="space-y-2">
                            <Label htmlFor="severity" className="font-medium flex items-center gap-2">
                              <Activity className="h-4 w-4 text-muted-foreground" /> Overall Severity
                            </Label>
                            <select id="severity" name="severity" value={formData.severity} onChange={handleInputChange}
                              className="flex h-11 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring shadow-sm">
                              <option value="">Select severity...</option>
                              <option value="mild">Mild (Annoying but manageable)</option>
                              <option value="moderate">Moderate (Affects daily activities)</option>
                              <option value="severe">Severe (Unable to perform daily tasks)</option>
                            </select>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>

                  {/* Free-text symptom input */}
                  <motion.div variants={itemVariants}>
                    <Card className="mb-6 shadow-sm border-primary/30 border-2">
                      <CardHeader className="pb-3">
                        <CardTitle className="flex items-center gap-2 text-base">
                          <Wand2 className="h-5 w-5 text-primary" />
                          Describe your symptoms in your own words
                        </CardTitle>
                        <CardDescription>
                          Type naturally — e.g. "I have a headche and running nose" — and we will match them automatically.
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="flex gap-2">
                          <Input
                            value={freeText}
                            onChange={e => setFreeText(e.target.value)}
                            onKeyDown={handleFreeTextKeyDown}
                            placeholder='e.g. "feaver and body ache" or "diarrhoea with vomiting"'
                            className="h-11 flex-1"
                            disabled={normalizing}
                          />
                          <Button type="button" onClick={handleNormalizeText} disabled={normalizing || !freeText.trim()} className="h-11 px-5 shrink-0">
                            {normalizing ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Add'}
                          </Button>
                        </div>
                        <p className="text-xs text-muted-foreground mt-2">
                          Handles misspellings, local names, and connectives like "and", "with", "also".
                        </p>
                      </CardContent>
                    </Card>
                  </motion.div>

                  {/* Search Bar */}
                  <motion.div variants={itemVariants} className="mb-4 relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                    <Input
                      type="text"
                      placeholder="Search symptoms by name..."
                      value={searchQuery}
                      onChange={e => setSearchQuery(e.target.value)}
                      className="pl-12 h-12 text-base bg-background shadow-sm"
                    />
                  </motion.div>

                  {/* Selected counter */}
                  {selectedSymptoms.length > 0 && (
                    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
                      className="mb-4 rounded-lg border border-primary/20 bg-primary/10 p-3">
                      <div className="flex items-center gap-2">
                        <motion.div animate={{ scale: [1, 1.15, 1] }} transition={{ duration: 1.8, repeat: Infinity }}>
                          <Target className="h-5 w-5 text-primary" />
                        </motion.div>
                        <span className="font-medium">
                          {selectedSymptoms.length} clue{selectedSymptoms.length !== 1 ? 's' : ''} locked in. Scan charge is {scanProgress}%.
                        </span>
                      </div>
                    </motion.div>
                  )}

                  {/* Symptom lists */}
                  {searchQuery.length > 0 ? (
                    <motion.div variants={itemVariants}>
                      <Card className="mb-6 border-2 border-primary/20 shadow-md">
                        <CardHeader className="pb-3 border-b"><CardTitle>Search Results</CardTitle></CardHeader>
                        <CardContent className="pt-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                            {filteredSymptoms.map(symptom => (
                              renderSymptomTile(symptom, 's')
                            ))}
                          </div>
                          {filteredSymptoms.length === 0 && (
                            <p className="text-muted-foreground text-center py-6">No symptoms found. Try describing them in the text box above.</p>
                          )}
                        </CardContent>
                      </Card>
                    </motion.div>
                  ) : (
                    Object.entries(CATEGORIES_MAP).map(([category, symptoms]) => (
                      <motion.div key={category} variants={itemVariants}>
                        <Card className={`mb-6 overflow-hidden border-2 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-lg ${CATEGORY_META[category]?.border || 'border-border'}`}>
                          <CardHeader className={`${CATEGORY_META[category]?.bg || 'bg-muted/30'} border-b pb-4 py-4`}>
                            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                              <div>
                                <CardTitle className="flex items-center gap-2 text-lg font-semibold">
                                  {(() => {
                                    const Icon = CATEGORY_META[category]?.icon || Activity;
                                    return <Icon className={`h-5 w-5 ${CATEGORY_META[category]?.accent || 'text-primary'}`} />;
                                  })()}
                                  {category}
                                </CardTitle>
                                <CardDescription className="mt-2 max-w-2xl">
                                  {CATEGORY_META[category]?.comment}
                                </CardDescription>
                              </div>
                              <Badge variant="outline" className="w-fit gap-1 bg-background/80">
                                <Target className="h-3.5 w-3.5" />
                                {categoryStats.find(item => item.category === category)?.count || 0} selected
                              </Badge>
                            </div>
                          </CardHeader>
                          <CardContent className="pt-4">
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                              {symptoms.map(symptom => {
                                if (!allSymptoms.includes(symptom)) return null;
                                return renderSymptomTile(symptom, 'c');
                              })}
                            </div>
                          </CardContent>
                        </Card>
                      </motion.div>
                    ))
                  )}

                  {/* Sticky selected bar */}
                  {selectedSymptoms.length > 0 && (
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="sticky bottom-4 z-20 mx-auto w-full">
                      <Card className="mb-4 border-primary/50 bg-background/95 backdrop-blur shadow-2xl">
                        <div className="p-3 px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
                          <div className="flex-1 overflow-x-auto whitespace-nowrap py-1 flex items-center gap-2">
                            <span className="text-sm font-semibold mr-2 shrink-0">Selected ({selectedSymptoms.length}):</span>
                            {selectedSymptoms.map(symptom => (
                              <span key={symptom}
                                className="inline-flex items-center px-3 py-1 bg-primary text-primary-foreground rounded-full text-xs font-medium cursor-pointer hover:bg-destructive hover:text-destructive-foreground transition-colors shrink-0"
                                onClick={() => handleSymptomToggle(symptom)}>
                                {symptom} <span className="ml-1 opacity-70">x</span>
                              </span>
                            ))}
                          </div>
                        </div>
                      </Card>
                    </motion.div>
                  )}

                  <motion.div variants={itemVariants} className="flex justify-center mt-8 pb-16">
                    <Button type="submit" size="lg" disabled={loading} className="w-full sm:w-auto px-12 h-14 text-lg font-bold shadow-xl gap-2">
                      {loading ? <><Loader2 className="h-6 w-6 animate-spin" />Analyzing scan...</> : <><Sparkles className="h-5 w-5" /> Launch Diagnosis Scan</>}
                    </Button>
                  </motion.div>
                </form>
              </motion.div>
            )}

            {/* ── STEP 2: Clarifying Questions ─────────────────────────────── */}
            {step === 2 && (
              <motion.div key="step2" variants={containerVariants} initial="hidden" animate="visible" exit="exit">
                <motion.div variants={itemVariants}>
                  <Card className="mb-6 shadow-md border-t-4 border-t-primary">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <HelpCircle className="h-5 w-5 text-primary" />
                        A few follow-up questions
                      </CardTitle>
                      <CardDescription>
                        Your symptoms could match several conditions. These questions help narrow down the most likely diagnosis.
                        Answer only what you know — you can skip any question.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {clarifyQuestions.map((q, i) => (
                        <motion.div key={q.symptom} variants={itemVariants}
                          className={`p-4 rounded-xl border-2 transition-colors ${clarifyAnswers[q.symptom] === 'yes' ? 'border-green-500 bg-green-50 dark:bg-green-950/20' : clarifyAnswers[q.symptom] === 'no' ? 'border-muted bg-muted/30' : 'border-border bg-background'}`}>
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                              <p className="text-sm text-muted-foreground mb-1">Question {i + 1} of {clarifyQuestions.length}</p>
                              <p className="font-medium text-foreground">{q.question}</p>
                              {q.helps_distinguish?.length > 0 && (
                                <p className="text-xs text-muted-foreground mt-1">
                                  Helps distinguish: {q.helps_distinguish.join(', ')}
                                </p>
                              )}
                            </div>
                            <div className="flex gap-2 shrink-0">
                              <Button type="button" size="sm" variant={clarifyAnswers[q.symptom] === 'yes' ? 'default' : 'outline'}
                                className={`gap-1 ${clarifyAnswers[q.symptom] === 'yes' ? 'bg-green-600 hover:bg-green-700 text-white border-green-600' : ''}`}
                                onClick={() => setClarifyAnswers(prev => ({ ...prev, [q.symptom]: prev[q.symptom] === 'yes' ? undefined : 'yes' }))}>
                                <CheckCircle2 className="h-4 w-4" /> Yes
                              </Button>
                              <Button type="button" size="sm" variant={clarifyAnswers[q.symptom] === 'no' ? 'secondary' : 'outline'}
                                className="gap-1"
                                onClick={() => setClarifyAnswers(prev => ({ ...prev, [q.symptom]: prev[q.symptom] === 'no' ? undefined : 'no' }))}>
                                <XCircle className="h-4 w-4" /> No
                              </Button>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </CardContent>
                  </Card>
                </motion.div>

                <motion.div variants={itemVariants} className="flex flex-col sm:flex-row gap-4 justify-center pb-16">
                  <Button type="button" variant="outline" size="lg" className="h-12 px-8"
                    onClick={() => setStep(1)}>
                    Back to Symptoms
                  </Button>
                  <Button type="button" size="lg" disabled={loading} className="h-12 px-12 font-bold shadow-xl"
                    onClick={handleFinalSubmit}>
                    {loading ? <><Loader2 className="mr-2 h-5 w-5 animate-spin" />Getting results...</> : 'Get Final Diagnosis'}
                  </Button>
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
