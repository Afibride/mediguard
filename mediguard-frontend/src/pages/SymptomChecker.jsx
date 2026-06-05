import React, { useState, useEffect, useRef } from 'react';
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
  ChevronRight, ChevronLeft, SkipForward, Star, Flame, ImagePlus, X,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { getAllSymptoms, diseases as diseaseDB } from '@/data/diseases';
import { getSymptoms, predictDisease, normalizeSymptoms, getClarifyQuestions, analyzeImage } from '@/services/api';
import { SYMPTOM_PLAIN_NAMES } from '@/data/layman';
import DisclaimerBanner from '@/components/DisclaimerBanner';
import SeasonalBanner from '@/components/SeasonalBanner';
import VoiceInput from '@/components/VoiceInput';
import { useLanguage } from '@/contexts/LanguageContext';

// ─── Cardinal Symptoms (mirrors backend app/data.py CARDINAL_SYMPTOMS) ───────
// At least ONE cardinal symptom must be present for the disease to appear.
// This prevents false positives like Tetanus appearing when user only has fever.
const CARDINAL_SYMPTOMS_MAP = {
  Tetanus:                  ['Jaw stiffness'],
  Meningitis:               ['Stiff neck'],
  Epilepsy:                 ['Seizures'],
  Migraine:                 ['Severe headache'],
  Tuberculosis:             ['Chronic cough'],
  Asthma:                   ['Wheezing', 'Chest tightness'],
  Cholera:                  ['Profuse watery diarrhea'],
  Dysentery:                ['Bloody or mucus-filled diarrhea'],
  Appendicitis:             ['Abdominal pain'],
  Chickenpox:               ['Itchy rash', 'Blisters'],
  Measles:                  ['Rash'],
  Scabies:                  ['Severe itching'],
  Ringworm:                 ['Ring-shaped rash'],
  'Herpes Zoster':          ['Blisters', 'Rash'],
  'Skin Fungal Infection':  ['Itchy skin', 'Ring-shaped rash', 'Red scaly skin'],
  Conjunctivitis:           ['Red eyes', 'Eye discharge'],
  'Diabetes Mellitus':      ['Increased thirst', 'Frequent urination'],
  'Hepatitis A':            ['Jaundice', 'Dark urine'],
  'Hepatitis B':            ['Jaundice', 'Yellow eyes', 'Dark urine'],
  'Yellow Fever':           ['Jaundice', 'Yellow eyes'],
  Onchocerciasis:           ['Severe itching'],
  Filariasis:               ['Swollen feet'],
  'Cystitis UTI':           ['Painful urination', 'Frequent urination'],
  'Kidney Stones':          ['Back pain'],
  'Pelvic Inflammatory Disease': ['Pelvic pain'],
  Tonsillitis:              ['Sore throat'],
  Diphtheria:               ['Sore throat', 'Hoarse voice', 'Difficulty swallowing'],
  Mumps:                    ['Jaw stiffness', 'Swollen lymph nodes'],
  Gonorrhea:                ['Genital discharge'],
  Syphilis:                 ['Genital sores'],
  Chlamydia:                ['Genital discharge', 'Vaginal discharge', 'Painful urination', 'Pelvic pain'],
  'Genital Herpes':         ['Genital sores', 'Blisters'],
  Trichomoniasis:           ['Vaginal itching', 'Genital discharge'],
};

/** Returns true if the symptom list satisfies the disease's cardinal requirement. */
const meetsCardinalRequirement = (diseaseName, selectedSymptoms) => {
  const cardinals = CARDINAL_SYMPTOMS_MAP[diseaseName];
  if (!cardinals) return true; // No cardinal requirement — always allowed
  const selectedLower = new Set(selectedSymptoms.map(s => s.toLowerCase()));
  return cardinals.some(c => selectedLower.has(c.toLowerCase()));
};

// ─── Static Data ─────────────────────────────────────────────────────────────

const CATEGORIES_MAP = {
  'Fever & Systemic': ['Fever', 'High fever', 'Prolonged fever', 'Sudden high fever', 'Mild fever', 'Chills', 'Sweating', 'Night sweats', 'Fatigue', 'Weakness', 'Weight loss', 'Swollen lymph nodes', 'Body aches'],
  'Respiratory': ['Cough', 'Chronic cough', 'Shortness of breath', 'Chest pain', 'Chest tightness', 'Runny nose', 'Sore throat', 'Nasal congestion', 'Coughing up blood', 'Wheezing', 'Hoarse voice'],
  'Gastrointestinal': ['Nausea', 'Vomiting', 'Diarrhea', 'Profuse watery diarrhea', 'Bloody or mucus-filled diarrhea', 'Abdominal pain', 'Lower abdominal pain', 'Constipation', 'Loss of appetite', 'Bloating', 'Heartburn', 'Jaundice'],
  'Pain & Neurological': ['Headache', 'Severe headache', 'Joint pain', 'Muscle aches', 'Back pain', 'Stiff neck', 'Confusion', 'Dizziness', 'Seizures', 'Numbness', 'Sensitivity to light', 'Jaw stiffness', 'Ear pain', 'Facial pain'],
  'Skin & Eyes': ['Rash', 'Itchy rash', 'Itchy skin', 'Ring-shaped rash', 'Blisters', 'Skin lesions', 'Skin sores', 'Pale skin', 'Red eyes', 'Yellow eyes', 'Eye discharge', 'Pus or discharge', 'Hair loss'],
  'Urinary & Reproductive': ['Frequent urination', 'Painful urination', 'Blood in urine', 'Pelvic pain', 'Vaginal discharge', 'Vaginal itching', 'Vaginal bleeding', 'Missed period', 'Breast pain', 'Breast tenderness', 'Morning sickness', 'Food cravings', 'Reduced fetal movement', 'Leaking fluid', 'Contractions', 'Face swelling', 'Hand swelling', 'Severe abdominal pain', 'Vision changes', 'Pain during intercourse', 'Genital sores', 'Genital discharge'],
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

// ─── SymptomTile — defined OUTSIDE SymptomChecker so React never unmounts it
// on symptom selection changes (preventing spurious re-entry animations).
const SymptomTile = React.memo(({ symptom, isSelected, onToggle }) => (
  <motion.div
    whileHover={{ y: -3, scale: 1.03 }}
    whileTap={{ scale: 0.94 }}
    onClick={() => onToggle(symptom)}
    className={`relative cursor-pointer select-none rounded-xl border-2 p-2.5 sm:p-3 min-h-[60px] sm:min-h-[68px] flex items-center gap-2 sm:gap-3 transition-colors ${
      isSelected
        ? 'border-primary bg-primary/10 ring-2 ring-primary/30 shadow-md'
        : 'border-border/60 bg-background hover:border-primary/40 hover:bg-muted/30'
    }`}
  >
    <div className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 transition-all ${
      isSelected ? 'border-primary bg-primary' : 'border-muted-foreground/30'
    }`}>
      <AnimatePresence>
        {isSelected && (
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
    <span className="flex-1 min-w-0">
      <span className={`block text-xs sm:text-sm font-semibold leading-tight ${isSelected ? 'text-primary' : 'text-foreground'}`}>
        {symptom}
      </span>
      {SYMPTOM_PLAIN_NAMES[symptom] && (
        <span className="block text-[10px] text-muted-foreground leading-tight mt-0.5">
          {SYMPTOM_PLAIN_NAMES[symptom]}
        </span>
      )}
    </span>
    {isSelected && (
      <motion.div
        layoutId={`glow-${symptom}`}
        className="absolute inset-0 rounded-xl bg-primary/5 pointer-events-none"
      />
    )}
  </motion.div>
));

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

// tileVariants intentionally removed — tiles must not re-animate on symptom check.
// Entry animation is handled by the zone slider (zoneVariants) on zone transitions only.

// ─── Component ────────────────────────────────────────────────────────────────

const SymptomChecker = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { t } = useLanguage();
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
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [imageAnalysis, setImageAnalysis] = useState(null);
  const [analyzingImage, setAnalyzingImage] = useState(false);
  const imgInputRef = useRef(null);

  // Child mode & voice input
  const [childMode, setChildMode] = useState(false);
  const [voiceListening, setVoiceListening] = useState(false);

  // Personal info
  const [formData, setFormData] = useState({
    duration: '', severity: '', gender: '', age: '',
    isPregnant: false, pregnancyWeeks: '', fatigueContext: false,
  });
  const [showPregnancyOption, setShowPregnancyOption] = useState(false);

  /** Convert a numeric age string to a backend age_group bucket. */
  const getAgeGroup = (ageStr) => {
    const n = parseInt(ageStr, 10);
    if (isNaN(n) || n < 0) return null;
    if (n <= 10) return '0-10';
    if (n <= 20) return '11-20';
    if (n <= 30) return '21-30';
    if (n <= 40) return '31-40';
    if (n <= 50) return '41-50';
    if (n <= 60) return '51-60';
    return '60+';
  };
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

  const handleNormalizeText = async (overrideText) => {
    const text = (typeof overrideText === 'string' ? overrideText : freeText).trim();
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

  /** Voice transcript — prepend child prefix if child mode is active, then auto-normalise */
  const handleVoiceTranscript = (transcript) => {
    const text = childMode ? `My child: ${transcript}` : transcript;
    setFreeText(text);
    // Small delay so state settles, then normalise immediately
    setTimeout(() => handleNormalizeText(text), 400);
  };

  const handleAnalyzeImage = async () => {
    if (!imageFile) return;
    setAnalyzingImage(true);
    setImageAnalysis(null);
    try {
      const res = await analyzeImage(imageFile, freeText.trim());
      setImageAnalysis(res.data.analysis);
    } catch (err) {
      const raw = err?.response?.data?.detail || err?.message || '';
      const isQuota = raw.includes('quota') || raw.includes('429') || raw.includes('unavailable');
      const description = isQuota
        ? 'Image analysis is temporarily unavailable (AI vision quota reached). Please select your symptoms manually instead.'
        : 'Could not analyse the image. Please try again or select symptoms manually.';
      toast({ variant: 'destructive', title: 'Image analysis failed', description });
    } finally {
      setAnalyzingImage(false);
    }
  };

  const handleImageFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    setImageAnalysis(null);
    const reader = new FileReader();
    reader.onload = (ev) => setImagePreview(ev.target.result);
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  const clearImage = () => {
    setImageFile(null);
    setImagePreview(null);
    setImageAnalysis(null);
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
      // Cardinal symptom gate: disease must have at least one cardinal symptom present
      .filter(d => meetsCardinalRequirement(d.name, symptomsToAnalyze))
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
        age_group: getAgeGroup(formData.age),
        is_pregnant: formData.isPregnant,
        pregnancy_weeks: formData.pregnancyWeeks ? Number(formData.pregnancyWeeks) : null,
        fatigue_context: formData.fatigueContext,
        child_mode: childMode,
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
        age_group: getAgeGroup(formData.age),
        is_pregnant: formData.isPregnant,
        pregnancy_weeks: formData.pregnancyWeeks ? Number(formData.pregnancyWeeks) : null,
        fatigue_context: formData.fatigueContext,
        child_mode: childMode,
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
    childMode,
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
  const scanRank = selectedSymptoms.length >= 6 ? t('sc_deep_scan') : selectedSymptoms.length >= 3 ? t('sc_good_signal') : selectedSymptoms.length >= 1 ? t('sc_signal') : t('sc_awaiting');

  // SymptomTile is defined outside this component (above) to prevent remounting
  // on every selectedSymptoms state change. Pass isSelected + onToggle as stable props.

  // ─── Zone Mini-Map ─────────────────────────────────────────────────────────

  const ZoneMap = () => (
    <div className="flex items-center justify-start sm:justify-center flex-nowrap gap-1 py-3 px-2">
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
              className="relative shrink-0"
            >
              <div className={`w-8 h-8 sm:w-9 sm:h-9 rounded-full flex items-center justify-center border-2 transition-all duration-200 ${
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
                      <Icon className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-primary" />
                    </motion.div>
                  : <Icon className={`h-3.5 w-3.5 sm:h-4 sm:w-4 ${isActive ? (CATEGORY_META[cat]?.accent || 'text-primary') : 'text-muted-foreground/60'}`} />
                }
              </div>
              {hasSelection && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute -top-1 -right-1 w-3.5 h-3.5 sm:w-4 sm:h-4 bg-primary rounded-full flex items-center justify-center shadow"
                >
                  <span className="text-[7px] sm:text-[8px] font-bold text-primary-foreground">{stat.count}</span>
                </motion.div>
              )}
            </motion.button>
            {i < CATEGORIES.length - 1 && (
              <div className={`h-0.5 w-3 sm:w-4 rounded-full transition-all duration-300 shrink-0 ${i < categoryStep ? 'bg-primary/60' : 'bg-border/40'}`} />
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
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=yes" />
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
              <div className="flex items-center gap-2 sm:gap-3 rounded-2xl bg-primary px-4 sm:px-8 py-3 sm:py-4 text-primary-foreground shadow-2xl">
                <Star className="h-5 w-5 sm:h-6 sm:w-6 fill-current" />
                <span className="text-lg sm:text-xl font-bold">Zone Cleared!</span>
                <Star className="h-5 w-5 sm:h-6 sm:w-6 fill-current" />
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <div className="min-h-screen bg-[linear-gradient(180deg,hsl(var(--muted)/0.45),hsl(var(--background))_38%,hsl(var(--muted)/0.25))] py-6 sm:py-8 md:py-12">
        <div className="container mx-auto px-3 sm:px-4 max-w-5xl">

          {/* ── Global Header ─────────────────────────────────────────────── */}
          <div className="mb-4 sm:mb-5 overflow-hidden rounded-xl sm:rounded-2xl border bg-background shadow-sm">
            {/* Main title row - improved for mobile */}
            <div className="flex flex-col xs:flex-row items-start xs:items-center gap-3 p-3 sm:p-5">
              <div className="flex items-center gap-3 w-full xs:w-auto">
                <motion.div
                  animate={{ rotate: [0, -6, 6, 0], scale: [1, 1.06, 1] }}
                  transition={{ duration: 3, repeat: Infinity, repeatDelay: 1.5 }}
                  className="flex h-10 w-10 sm:h-12 sm:w-12 shrink-0 items-center justify-center rounded-full bg-primary/10"
                >
                  <Thermometer className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />
                </motion.div>
                <div className="flex-1 min-w-0">
                  <h1 className="text-xl sm:text-2xl font-bold text-foreground">
                    {t('sc_title')}
                  </h1>
                </div>
              </div>
              
              {/* Badges - wrap on mobile */}
              <div className="flex items-center justify-between xs:justify-end gap-2 w-full xs:w-auto">
                <Badge className="gap-1 bg-primary/10 text-primary hover:bg-primary/10 text-[10px] sm:text-xs">
                  <ShieldCheck className="h-2.5 w-2.5 sm:h-3 sm:w-3" />Guided
                </Badge>
                <motion.div key={scanRank} initial={{ opacity: 0, scale: 0.85 }} animate={{ opacity: 1, scale: 1 }}>
                  <Badge variant="outline" className="gap-1 text-[10px] sm:text-xs whitespace-nowrap">
                    <Flame className={`h-2.5 w-2.5 sm:h-3 sm:w-3 ${selectedSymptoms.length >= 3 ? 'text-orange-500' : 'text-muted-foreground'}`} />
                    <span className="hidden xs:inline">{scanRank}</span>
                    <span className="xs:hidden">{scanRank.substring(0, 10)}...</span>
                  </Badge>
                </motion.div>
              </div>
            </div>
            
            {/* Description - hidden on mobile */}
            <p className="mt-0.5 text-sm text-muted-foreground leading-snug hidden sm:block px-5 pb-3">
              Move through symptom zones, collect clues, then launch the diagnosis scan.
            </p>

            {/* Scan charge bar — compact inline strip */}
            <div className="border-t bg-muted/30 px-3 sm:px-4 py-2 flex items-center gap-2 sm:gap-3">
              <span className="text-[10px] sm:text-xs font-semibold text-muted-foreground shrink-0">Scan charge</span>
              <div className="flex-1 h-1.5 sm:h-2 overflow-hidden rounded-full bg-muted">
                <motion.div
                  className="h-full rounded-full bg-gradient-to-r from-primary to-primary/70"
                  initial={false}
                  animate={{ width: `${scanProgress}%` }}
                  transition={{ type: 'spring', stiffness: 80, damping: 18 }}
                />
              </div>
              <motion.span key={scanProgress} initial={{ scale: 1.3 }} animate={{ scale: 1 }}
                className="text-[10px] sm:text-xs font-bold text-primary shrink-0">{scanProgress}%</motion.span>
              {selectedSymptoms.length > 0 && (
                <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}>
                  <Badge className="gap-1 bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300 text-[9px] sm:text-xs shrink-0 px-1.5 sm:px-2">
                    <Trophy className="h-2 w-2 sm:h-3 sm:w-3" />{selectedSymptoms.length}
                  </Badge>
                </motion.div>
              )}
            </div>
          </div>

          {/* ── Global Step Indicator ──────────────────────────────────────── */}
          <div className="flex items-center justify-center gap-2 sm:gap-4 mb-4 sm:mb-6">
            {['Symptom Zones', 'Follow-up Questions'].map((label, i) => {
              const idx = i + 1;
              const active = step === idx;
              const done = step > idx;
              return (
                <React.Fragment key={label}>
                  <div className="flex items-center gap-1 sm:gap-2">
                    <div className={`w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center text-xs sm:text-sm font-bold border-2 transition-all ${
                      done ? 'bg-primary border-primary text-primary-foreground' : 
                      active ? 'bg-primary/10 border-primary text-primary scale-110 shadow-sm' : 
                      'bg-muted border-muted-foreground/30 text-muted-foreground'
                    }`}>
                      {done ? <CheckCircle2 className="h-3.5 w-3.5 sm:h-4 sm:w-4" /> : idx}
                    </div>
                    <span className={`text-[10px] sm:text-sm font-medium ${active ? 'text-primary' : done ? 'text-foreground' : 'text-muted-foreground'} hidden xs:inline`}>
                      {label}
                    </span>
                    <span className={`text-[10px] sm:text-sm font-medium ${active ? 'text-primary' : done ? 'text-foreground' : 'text-muted-foreground'} xs:hidden`}>
                      {i === 0 ? 'Zones' : 'Qs'}
                    </span>
                  </div>
                  {i < 1 && <div className={`flex-1 max-w-10 sm:max-w-16 h-0.5 rounded-full ${step > 1 ? 'bg-primary' : 'bg-muted-foreground/20'}`} />}
                </React.Fragment>
              );
            })}
          </div>

          <SeasonalBanner className="mb-4 sm:mb-5" />
          <DisclaimerBanner variant="warning" className="mb-4 sm:mb-6" />

          {/* ── Main Content ───────────────────────────────────────────────── */}
          <AnimatePresence mode="wait">

            {/* ════════════════ STEP 1: Symptom Zones ════════════════ */}
            {step === 1 && (
              <motion.div key="step1" variants={containerVariants} initial="hidden" animate="visible" exit="exit">
                <form onSubmit={handleInitialSubmit}>

                  {/* Personal Info (collapsible) */}
                  <motion.div variants={itemVariants} className="mb-4 sm:mb-5">
                    <button
                      type="button"
                      onClick={() => setShowPersonalInfo(v => !v)}
                      className="w-full flex items-center justify-between px-4 sm:px-5 py-2.5 sm:py-3 rounded-xl border bg-background hover:bg-muted/40 transition-colors text-left"
                    >
                      <span className="flex items-center gap-2 font-semibold text-xs sm:text-sm">
                        <User className="h-4 w-4 text-primary" />
                        Personal Info <span className="hidden xs:inline">(Optional — improves accuracy)</span>
                        <span className="xs:hidden text-muted-foreground font-normal">(optional)</span>
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
                            <CardContent className="pt-4 sm:pt-5">
                              {/* Gender and Age - stacked on mobile, side by side on tablet+ */}
                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-5">
                                <div className="space-y-2">
                                  <Label className="font-medium text-sm">Gender</Label>
                                  <RadioGroup name="gender" value={formData.gender}
                                    onValueChange={v => setFormData(prev => ({ ...prev, gender: v }))}
                                    className="flex gap-3 sm:gap-4">
                                    {['male', 'female', 'other'].map(g => (
                                      <div key={g} className="flex items-center gap-1.5 sm:gap-2">
                                        <RadioGroupItem value={g} id={g} />
                                        <Label htmlFor={g} className="capitalize cursor-pointer text-sm">{g}</Label>
                                      </div>
                                    ))}
                                  </RadioGroup>
                                </div>
                                <div className="space-y-2">
                                  <Label htmlFor="age" className="font-medium text-sm">Age</Label>
                                  <Input id="age" name="age" type="number" min="0" max="120"
                                    value={formData.age} onChange={handleInputChange} placeholder="Your age" className="h-9 sm:h-10" />
                                </div>
                              </div>

                              {showPregnancyOption && (
                                <div className="mt-3 grid grid-cols-1 sm:grid-cols-[1fr_160px] gap-3 p-3 sm:p-4 bg-pink-50 dark:bg-pink-950/20 rounded-lg border border-pink-200 dark:border-pink-900/50">
                                  <div className="flex items-center gap-2">
                                    <Checkbox id="isPregnant" checked={formData.isPregnant}
                                      onCheckedChange={checked => setFormData(prev => ({ ...prev, isPregnant: checked, pregnancyWeeks: checked ? prev.pregnancyWeeks : '' }))} />
                                    <Label htmlFor="isPregnant" className="flex items-center gap-2 cursor-pointer font-medium text-sm">
                                      <Baby className="h-4 w-4 text-pink-500" />Currently pregnant
                                    </Label>
                                  </div>
                                  <Input name="pregnancyWeeks" type="number" min="1" max="42"
                                    value={formData.pregnancyWeeks} onChange={handleInputChange}
                                    disabled={!formData.isPregnant} placeholder="Weeks" className="h-9 sm:h-10" />
                                </div>
                              )}

                              {/* Child mode toggle */}
                              <div className="mt-3 p-3 rounded-lg border border-rose-200 bg-rose-50 dark:border-rose-900/50 dark:bg-rose-950/20 flex items-start gap-2 sm:gap-3">
                                <Checkbox id="childMode" checked={childMode}
                                  onCheckedChange={checked => setChildMode(!!checked)} className="mt-0.5 shrink-0" />
                                <Label htmlFor="childMode" className="cursor-pointer text-xs sm:text-sm flex-1">
                                  <span className="font-semibold flex items-center gap-1.5">
                                    <Baby className="h-3.5 w-3.5 text-rose-500" />
                                    <span className="hidden xs:inline">I am checking for a child (my pikin)</span>
                                    <span className="xs:hidden">Checking for a child?</span>
                                  </span>
                                  <span className="text-muted-foreground block mt-0.5 text-[10px] sm:text-xs hidden xs:block">
                                    Activates child health mode — paediatric dosing, EPI vaccination schedule, child danger signs.
                                  </span>
                                </Label>
                              </div>

                              <div className="mt-3 p-3 rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-900/50 dark:bg-amber-950/20 flex items-start gap-2 sm:gap-3">
                                <Checkbox id="fatigueContext" checked={formData.fatigueContext}
                                  onCheckedChange={checked => setFormData(prev => ({ ...prev, fatigueContext: checked }))} className="mt-0.5 shrink-0" />
                                <Label htmlFor="fatigueContext" className="cursor-pointer text-xs sm:text-sm">
                                  <span className="font-semibold flex items-center gap-1">
                                    <Brain className="h-3.5 w-3.5 text-amber-600" />
                                    <span className="hidden xs:inline">Symptoms may relate to fatigue, poor sleep, stress, or heavy activity</span>
                                    <span className="xs:hidden">Fatigue/stress related?</span>
                                  </span>
                                  <span className="text-muted-foreground block mt-0.5 text-[10px] sm:text-xs hidden xs:block">
                                    MediGuard will note this context while still checking for warning signs.
                                  </span>
                                </Label>
                              </div>

                              <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
                                <div className="space-y-2 min-w-0">
                                  <Label htmlFor="duration" className="font-medium text-sm">Symptom Duration</Label>
                                  <select id="duration" name="duration" value={formData.duration} onChange={handleInputChange}
                                    className="flex h-9 sm:h-10 w-full rounded-md border border-input bg-background px-2 sm:px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                                    <option value="">Select…</option>
                                    <option value="1-3 days">1–3 days</option>
                                    <option value="3-7 days">3–7 days</option>
                                    <option value="1-2 weeks">1–2 weeks</option>
                                    <option value="2+ weeks">More than 2 weeks</option>
                                  </select>
                                </div>
                                <div className="space-y-2 min-w-0">
                                  <Label htmlFor="severity" className="font-medium text-sm">Overall Severity</Label>
                                  <select id="severity" name="severity" value={formData.severity} onChange={handleInputChange}
                                    className="flex h-9 sm:h-10 w-full rounded-md border border-input bg-background px-2 sm:px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                                    <option value="">Select…</option>
                                    <option value="mild">Mild</option>
                                    <option value="moderate">Moderate</option>
                                    <option value="severe">Severe</option>
                                  </select>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>

                  {/* Child mode active indicator strip */}
                  <AnimatePresence>
                    {childMode && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mb-3 overflow-hidden"
                      >
                        <div className="flex items-center gap-2 rounded-lg border border-rose-300 bg-rose-50 dark:border-rose-800 dark:bg-rose-950/30 px-3 py-2">
                          <Baby className="h-4 w-4 text-rose-500 shrink-0" />
                          <span className="text-xs font-semibold text-rose-700 dark:text-rose-300">
                            Child mode active — all guidance uses paediatric context
                          </span>
                          <button type="button" onClick={() => setChildMode(false)} className="ml-auto text-rose-400 hover:text-rose-600">
                            <X className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Free-text input */}
                  <motion.div variants={itemVariants} className="mb-4 sm:mb-5">
                    <Card className="border-primary/30 border shadow-sm">
                      <CardContent className="pt-3 sm:pt-4 pb-3 sm:pb-4">
                        <div className="flex items-center gap-2 mb-2">
                          <Wand2 className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-primary" />
                          <span className="text-xs sm:text-sm font-semibold">{t('sc_describe_hint')}</span>
                          <span className="text-[10px] text-muted-foreground hidden xs:inline">(Pidgin, English, Français)</span>
                        </div>
                        {/* Pidgin / language examples */}
                        <p className="text-[9px] sm:text-[10px] text-muted-foreground mb-2 leading-relaxed hidden sm:block">
                          💬 Type in any language:&nbsp;
                          <em>"my head dey pain me"</em>,&nbsp;
                          <em>"belle dey do me"</em>,&nbsp;
                          <em>"j'ai de la fièvre"</em>,&nbsp;
                          <em>"fever and body ache"</em>
                        </p>
                        <div className="flex gap-2">
                          <Input
                            value={freeText}
                            onChange={e => setFreeText(e.target.value)}
                            onKeyDown={handleFreeTextKeyDown}
                            placeholder={childMode ? '"My pikin dey hot and vomit"' : '"my head dey pain me / fever and body ache"'}
                            className="h-9 sm:h-10 flex-1 text-sm"
                            disabled={normalizing || voiceListening}
                          />
                          {/* Voice input */}
                          <VoiceInput
                            onTranscript={handleVoiceTranscript}
                            onListening={setVoiceListening}
                            lang="en-NG"
                            disabled={normalizing}
                            size="sm"
                          />
                          <Button type="button" onClick={() => handleNormalizeText()} disabled={normalizing || !freeText.trim()} className="h-9 sm:h-10 px-3 sm:px-5 shrink-0 text-xs sm:text-sm">
                            {normalizing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <><Sparkles className="h-3 w-3 sm:h-3.5 sm:w-3.5 mr-1" />Add</>}
                          </Button>
                        </div>
                        {voiceListening && (
                          <p className="mt-1.5 text-[10px] text-rose-500 font-medium flex items-center gap-1">
                            <span className="inline-block w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
                            Listening… speak your symptoms now
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  </motion.div>

                  {/* Image upload for visual symptoms */}
                  <motion.div variants={itemVariants} className="mb-4 sm:mb-5">
                    <Card className="border-amber-300/60 border shadow-sm dark:border-amber-700/40">
                      <CardContent className="pt-3 sm:pt-4 pb-3 sm:pb-4">
                        <div className="flex items-center gap-2 mb-2 sm:mb-3">
                          <ImagePlus className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-amber-600" />
                          <span className="text-xs sm:text-sm font-semibold">{t('sc_upload_photo')}</span>
                          <span className="text-[10px] text-muted-foreground hidden xs:inline">(rash, skin lesion, eye, swelling…)</span>
                        </div>

                        {/* Hidden file input */}
                        <input ref={imgInputRef} type="file" accept="image/jpeg,image/png,image/webp"
                          className="hidden" onChange={handleImageFileChange} />

                        {!imagePreview ? (
                          <button type="button" onClick={() => imgInputRef.current?.click()}
                            className="w-full border-2 border-dashed border-amber-300 dark:border-amber-700/50 rounded-xl p-4 sm:p-6 flex flex-col items-center gap-2 text-muted-foreground hover:border-primary hover:text-primary transition-colors">
                            <ImagePlus className="h-6 w-6 sm:h-8 sm:w-8" />
                            <span className="text-xs sm:text-sm font-medium">Tap to upload photo</span>
                            <span className="text-[9px] sm:text-xs">JPEG, PNG or WebP · max 10 MB</span>
                          </button>
                        ) : (
                          <div className="space-y-3">
                            <div className="flex flex-col xs:flex-row items-start gap-3">
                              <img src={imagePreview} alt="symptom" className="h-24 w-24 sm:h-28 sm:w-28 rounded-lg object-cover border shadow-sm shrink-0" />
                              <div className="flex-1 min-w-0 space-y-2">
                                <p className="text-[10px] sm:text-xs text-muted-foreground truncate">{imageFile?.name}</p>
                                <Button type="button" size="sm" onClick={handleAnalyzeImage}
                                  disabled={analyzingImage}
                                  className="gap-1.5 bg-amber-600 hover:bg-amber-700 text-white w-full sm:w-auto text-xs sm:text-sm">
                                  {analyzingImage
                                    ? <><Loader2 className="h-3 w-3 animate-spin" />{t('sc_analysing')}</>
                                    : <><Sparkles className="h-3 w-3" />{t('sc_analyse')}</>
                                  }
                                </Button>
                                <button type="button" onClick={clearImage}
                                  className="flex items-center gap-1 text-[10px] sm:text-xs text-destructive hover:underline">
                                  <X className="h-3 w-3" />Remove
                                </button>
                              </div>
                            </div>

                            {imageAnalysis && (
                              <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
                                className="p-2 sm:p-3 bg-amber-50 dark:bg-amber-950/20 rounded-lg border border-amber-200 dark:border-amber-800 text-xs sm:text-sm space-y-1">
                                <p className="font-semibold text-amber-800 dark:text-amber-300 flex items-center gap-1.5 text-xs sm:text-sm">
                                  <Sparkles className="h-3 w-3 sm:h-4 sm:w-4" />Image Analysis
                                </p>
                                <p className="text-foreground/80 whitespace-pre-wrap text-[10px] sm:text-xs leading-relaxed">{imageAnalysis}</p>
                                <p className="text-[8px] sm:text-[10px] text-muted-foreground">Not a diagnosis — always confirm with a healthcare professional.</p>
                              </motion.div>
                            )}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </motion.div>

                  {/* Search input */}
                  <motion.div variants={itemVariants} className="mb-4 sm:mb-5 relative">
                    <Search className="absolute left-3 sm:left-4 top-1/2 -translate-y-1/2 h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground" />
                    <Input
                      type="text"
                      placeholder={t('sc_search')}
                      value={searchQuery}
                      onChange={e => setSearchQuery(e.target.value)}
                      className="pl-9 sm:pl-12 h-10 sm:h-11 bg-background shadow-sm text-sm"
                    />
                    {searchQuery && (
                      <button type="button" onClick={() => setSearchQuery('')}
                        className="absolute right-3 sm:right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                        <XCircle className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                      </button>
                    )}
                  </motion.div>

                  {/* ── Search results OR Zone slider ── */}
                  <AnimatePresence mode="wait">
                    {searchQuery.length > 0 ? (
                      <motion.div key="search" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                        <Card className="mb-6 border-2 border-primary/20 shadow-md">
                          <CardHeader className="pb-3 border-b">
                            <CardTitle className="text-sm sm:text-base">Search Results — {filteredSymptoms.length} found</CardTitle>
                          </CardHeader>
                          <CardContent className="pt-4">
                            <motion.div className="grid grid-cols-1 xs:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3" variants={containerVariants} initial="hidden" animate="visible">
                              {filteredSymptoms.map((symptom) => (
                                <SymptomTile
                                  key={symptom}
                                  symptom={symptom}
                                  isSelected={selectedSymptoms.includes(symptom)}
                                  onToggle={handleSymptomToggle}
                                />
                              ))}
                            </motion.div>
                            {filteredSymptoms.length === 0 && (
                              <p className="text-center py-6 sm:py-8 text-muted-foreground text-sm">No symptoms found. Try the text input above.</p>
                            )}
                          </CardContent>
                        </Card>
                      </motion.div>
                    ) : (
                      <motion.div key="zones" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                        {/* Zone Mini-Map */}
                        <div className="mb-4 rounded-xl border bg-background shadow-sm overflow-hidden">
                          <div className="px-3 sm:px-4 pt-3 pb-1 flex items-center justify-between">
                            <span className="text-xs sm:text-sm font-bold text-foreground">
                              Zone {categoryStep + 1} of {CATEGORIES.length}
                            </span>
                            <span className="text-[9px] sm:text-xs text-muted-foreground">Tap a zone to jump</span>
                          </div>
                          <div className="overflow-x-auto pb-1 scrollbar-thin">
                            <ZoneMap />
                          </div>
                        </div>

                        {/* Zone Slider */}
                        <div className="relative overflow-hidden rounded-xl sm:rounded-2xl border-2 shadow-lg" style={{ borderColor: `hsl(var(--border))` }}>
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
                              <div className={`${meta.bg || 'bg-muted/30'} border-b ${meta.border || 'border-border'} p-3 sm:p-5`}>
                                <div className="flex items-center justify-between gap-3">
                                  <div className="flex items-center gap-2 sm:gap-3">
                                    <motion.div
                                      initial={{ rotate: -20, scale: 0.7 }}
                                      animate={{ rotate: 0, scale: 1 }}
                                      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
                                      className={`flex h-10 w-10 sm:h-14 sm:w-14 shrink-0 items-center justify-center rounded-xl sm:rounded-2xl border-2 ${meta.border || 'border-border'} ${meta.bg || 'bg-muted/30'} shadow-sm`}
                                    >
                                      <ZoneIcon className={`h-4 w-4 sm:h-7 sm:w-7 ${meta.accent || 'text-primary'}`} />
                                    </motion.div>
                                    <div>
                                      <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                                        <Badge variant="outline" className="text-[9px] sm:text-xs font-bold bg-background/80">
                                          ZONE {categoryStep + 1}
                                        </Badge>
                                        {selectedInCurrentZone.length > 0 && (
                                          <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}>
                                            <Badge className="text-[9px] sm:text-xs bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">
                                              <Star className="h-2 w-2 sm:h-3 sm:w-3 mr-1 fill-current" />{selectedInCurrentZone.length} selected
                                            </Badge>
                                          </motion.div>
                                        )}
                                      </div>
                                      <h2 className={`text-sm sm:text-xl font-bold ${meta.accent || 'text-foreground'}`}>{currentCategory}</h2>
                                      <p className="text-[10px] sm:text-sm text-muted-foreground leading-snug hidden sm:block">{meta.comment}</p>
                                    </div>
                                  </div>
                                </div>
                              </div>

                              {/* Zone Symptom Grid */}
                              <div className="p-3 sm:p-5 bg-background">
                                <motion.div
                                  className="grid grid-cols-2 gap-2 sm:gap-3"
                                  variants={containerVariants}
                                  initial="hidden"
                                  animate="visible"
                                >
                                  {(CATEGORIES_MAP[currentCategory] || []).map((symptom) => {
                                    if (!allSymptoms.includes(symptom)) return null;
                                    return (
                                      <SymptomTile
                                        key={symptom}
                                        symptom={symptom}
                                        isSelected={selectedSymptoms.includes(symptom)}
                                        onToggle={handleSymptomToggle}
                                      />
                                    );
                                  })}
                                </motion.div>

                                {(CATEGORIES_MAP[currentCategory] || []).filter(s => allSymptoms.includes(s)).length === 0 && (
                                  <p className="text-center py-6 sm:py-8 text-muted-foreground text-sm">No symptoms available in this zone.</p>
                                )}
                              </div>

                              {/* Zone Navigation */}
                              <div className={`flex items-center justify-between gap-2 px-3 sm:px-5 py-2.5 sm:py-3 border-t ${meta.bg || 'bg-muted/20'}`}>
                                <Button
                                  type="button"
                                  variant="outline"
                                  size="sm"
                                  className="gap-1 h-8 sm:h-10 px-2 sm:px-4 text-xs sm:text-sm"
                                  onClick={goPrevZone}
                                  disabled={categoryStep === 0}
                                >
                                  <ChevronLeft className="h-3 w-3 sm:h-4 sm:w-4" />
                                  <span className="hidden sm:inline">Back</span>
                                </Button>

                                <div className="flex items-center gap-0.5 sm:gap-1">
                                  {CATEGORIES.map((_, i) => (
                                    <div key={i} className={`h-1 rounded-full transition-all duration-300 ${
                                      i === categoryStep ? 'w-3 sm:w-5 bg-primary' :
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
                                      className="gap-1 h-8 sm:h-10 px-2 sm:px-4 bg-gradient-to-r from-primary to-primary/80 shadow-lg text-xs sm:text-sm"
                                    >
                                      {loading
                                        ? <><Loader2 className="h-3 w-3 animate-spin" /></>
                                        : <><Sparkles className="h-3 w-3" /><span className="hidden sm:inline">{t('sc_launch')}</span></>
                                      }
                                    </Button>
                                  </motion.div>
                                ) : (
                                  <Button type="button" size="sm" onClick={goNextZone} className="gap-1 h-8 sm:h-10 px-2 sm:px-4 text-xs sm:text-sm">
                                    {selectedInCurrentZone.length > 0 ? (
                                      <><Star className="h-2.5 w-2.5 fill-current" /><span className="hidden xs:inline">{t('sc_next_zone')}</span><ChevronRight className="h-3 w-3" /></>
                                    ) : (
                                      <><SkipForward className="h-2.5 w-2.5" /><span className="hidden xs:inline">Skip</span><ChevronRight className="h-3 w-3" /></>
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
                        className="sticky bottom-3 sm:bottom-4 z-20 mt-4 sm:mt-6 px-1 sm:px-0"
                      >
                        <Card className="border-primary/50 bg-background/95 backdrop-blur shadow-2xl">
                          <div className="p-2 sm:p-3 px-3 sm:px-4 flex flex-col xs:flex-row items-center justify-between gap-2 sm:gap-3">
                            <div className="flex-1 overflow-x-auto whitespace-nowrap flex items-center gap-1.5 sm:gap-2 py-1 scrollbar-thin">
                              <span className="text-xs sm:text-sm font-semibold shrink-0 flex items-center gap-1 sm:gap-1.5">
                                <Target className="h-3 w-3 sm:h-4 sm:w-4 text-primary" />
                                <span className="hidden xs:inline">{selectedSymptoms.length} clue{selectedSymptoms.length !== 1 ? 's' : ''}:</span>
                                <span className="xs:hidden">{selectedSymptoms.length}</span>
                              </span>
                              {selectedSymptoms.slice(0, 3).map(symptom => (
                                <motion.span
                                  key={symptom}
                                  initial={{ scale: 0 }}
                                  animate={{ scale: 1 }}
                                  exit={{ scale: 0 }}
                                  className="inline-flex items-center px-1.5 sm:px-3 py-0.5 sm:py-1 bg-primary text-primary-foreground rounded-full text-[9px] sm:text-xs font-medium cursor-pointer hover:bg-destructive transition-colors shrink-0"
                                  onClick={() => handleSymptomToggle(symptom)}
                                >
                                  <span className="hidden xs:inline">{symptom}</span>
                                  <span className="xs:hidden">{symptom.substring(0, 10)}...</span>
                                  <XCircle className="ml-1 h-2 w-2 sm:h-3 sm:w-3 opacity-70" />
                                </motion.span>
                              ))}
                              {selectedSymptoms.length > 3 && (
                                <span className="text-[9px] sm:text-xs text-muted-foreground">
                                  +{selectedSymptoms.length - 3}
                                </span>
                              )}
                            </div>
                            {isLastZone && (
                              <Button type="submit" size="sm" disabled={loading} className="shrink-0 gap-1 h-7 sm:h-9 text-[10px] sm:text-xs">
                                {loading ? <Loader2 className="h-2.5 w-2.5 animate-spin" /> : <Sparkles className="h-2.5 w-2.5" />}
                                {loading ? t('sc_scanning') : t('sc_launch')}
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
                      className="mt-4 sm:mt-6 flex justify-center"
                    >
                      <Button type="submit" size="lg" disabled={loading}
                        className="gap-2 h-10 sm:h-12 px-6 sm:px-10 text-sm sm:text-base font-bold shadow-xl bg-gradient-to-r from-primary to-primary/80">
                        {loading
                          ? <><Loader2 className="h-4 w-4 animate-spin" />Analyzing…</>
                          : <><Sparkles className="h-4 w-4" />{t('sc_launch_full')}</>
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
                  <Card className="mb-4 sm:mb-6 shadow-md border-t-4 border-t-primary overflow-hidden">
                    <CardHeader className="bg-primary/5 p-4 sm:p-6">
                      <CardTitle className="flex items-center gap-2 text-base sm:text-lg">
                        <HelpCircle className="h-5 w-5 text-primary" />
                        A few follow-up questions
                      </CardTitle>
                      <CardDescription className="text-xs sm:text-sm">
                        Your symptoms could match several conditions. These yes/no questions help the model narrow it down.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="pt-4 sm:pt-5 space-y-3 sm:space-y-4">
                      {clarifyQuestions.map((q, i) => (
                        <motion.div
                          key={q.symptom}
                          variants={itemVariants}
                          whileHover={{ scale: 1.005 }}
                          className={`p-3 sm:p-4 rounded-xl border-2 transition-all duration-200 ${
                            clarifyAnswers[q.symptom] === 'yes'
                              ? 'border-green-400 bg-green-50 dark:bg-green-950/20 shadow-sm'
                              : clarifyAnswers[q.symptom] === 'no'
                                ? 'border-muted bg-muted/30'
                                : 'border-border bg-background'
                          }`}
                        >
                          <div className="flex flex-col xs:flex-row items-start justify-between gap-3 xs:gap-4">
                            <div className="flex-1">
                              <p className="text-[10px] sm:text-xs text-muted-foreground mb-1 font-medium">
                                Question {i + 1} of {clarifyQuestions.length}
                              </p>
                              <p className="font-semibold text-foreground text-sm sm:text-base">{q.question}</p>
                              {q.helps_distinguish?.length > 0 && (
                                <p className="text-[9px] sm:text-xs text-muted-foreground mt-1">
                                  Helps distinguish: {q.helps_distinguish.slice(0, 3).join(', ')}
                                  {q.helps_distinguish.length > 3 && '…'}
                                </p>
                              )}
                            </div>
                            <div className="flex gap-2 shrink-0">
                              <motion.div whileTap={{ scale: 0.9 }}>
                                <Button type="button" size="sm"
                                  variant={clarifyAnswers[q.symptom] === 'yes' ? 'default' : 'outline'}
                                  className={`gap-1 text-xs sm:text-sm ${clarifyAnswers[q.symptom] === 'yes' ? 'bg-green-600 hover:bg-green-700 text-white border-green-600' : ''}`}
                                  onClick={() => setClarifyAnswers(prev => ({ ...prev, [q.symptom]: prev[q.symptom] === 'yes' ? undefined : 'yes' }))}>
                                  <CheckCircle2 className="h-3.5 w-3.5" />Yes
                                </Button>
                              </motion.div>
                              <motion.div whileTap={{ scale: 0.9 }}>
                                <Button type="button" size="sm"
                                  variant={clarifyAnswers[q.symptom] === 'no' ? 'secondary' : 'outline'}
                                  className="gap-1 text-xs sm:text-sm"
                                  onClick={() => setClarifyAnswers(prev => ({ ...prev, [q.symptom]: prev[q.symptom] === 'no' ? undefined : 'no' }))}>
                                  <XCircle className="h-3.5 w-3.5" />No
                                </Button>
                              </motion.div>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </CardContent>
                  </Card>
                </motion.div>

                <motion.div variants={itemVariants} className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center pb-8 sm:pb-12">
                  <Button type="button" variant="outline" size="lg" className="h-10 sm:h-12 px-6 sm:px-8 gap-2 text-sm sm:text-base"
                    onClick={() => setStep(1)}>
                    <ChevronLeft className="h-4 w-4" />Back to Zones
                  </Button>
                  <motion.div
                    animate={{ scale: [1, 1.03, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <Button type="button" size="lg" disabled={loading} className="h-10 sm:h-12 px-8 sm:px-12 font-bold shadow-xl gap-2 text-sm sm:text-base"
                      onClick={handleFinalSubmit}>
                      {loading
                        ? <><Loader2 className="h-4 w-4 animate-spin" />Getting results…</>
                        : <><Sparkles className="h-4 w-4" />Get Final Diagnosis</>
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
