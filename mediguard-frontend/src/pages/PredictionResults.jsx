import React, { useEffect, useState } from 'react';
import { Helmet } from 'react-helmet';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { getCommonName } from '@/data/layman';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, ArrowLeft, MessageCircle, Info, HeartPulse, Activity, Stethoscope, Clock, ShieldAlert, Save, Brain, ChevronDown, CheckCircle2, Pill, AlertTriangle, Baby, User, Heart, HelpCircle, ThumbsUp, ThumbsDown, Shield, Microscope, Printer, FlaskConical } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/components/AuthContext';
import DisclaimerBanner from '@/components/DisclaimerBanner';
import NearbyFacilities from '@/components/NearbyFacilities';
import SpeakButton from '@/components/SpeakButton';
import { submitFeedback } from '@/services/api';

const DISEASE_TESTS = {
  'Malaria': ['Rapid Diagnostic Test (RDT)', 'Thick/thin blood film microscopy', 'Full Blood Count (FBC)', 'Haemoglobin level'],
  'Typhoid Fever': ['Widal test', 'Blood culture (gold standard)', 'Stool culture', 'Full Blood Count (FBC)'],
  'Tuberculosis': ['Sputum smear microscopy (AFB)', 'GeneXpert MTB/RIF', 'Chest X-ray', 'Tuberculin skin test (Mantoux)', 'Full Blood Count'],
  'HIV AIDS': ['HIV rapid antibody test', 'HIV ELISA / Western blot', 'CD4 count', 'Viral load', 'Full Blood Count'],
  'Hepatitis B': ['HBsAg test', 'Anti-HBs antibody', 'Liver function tests (LFT)', 'Abdominal ultrasound'],
  'Hypertension': ['Blood pressure measurement (multiple readings)', 'Urine dipstick (protein)', 'Renal function tests', 'Electrocardiogram (ECG)', 'Fundoscopy'],
  'Diabetes Mellitus': ['Fasting blood glucose', 'HbA1c (glycated haemoglobin)', 'Random blood glucose', 'Urine glucose & ketones', 'Renal function tests'],
  'Pneumonia': ['Chest X-ray', 'Full Blood Count', 'Sputum culture & sensitivity', 'Blood culture', 'SpO2 pulse oximetry'],
  'Cholera': ['Stool culture & sensitivity', 'Stool microscopy', 'Electrolytes (Na, K, Cl)', 'Urea and creatinine'],
  'Meningitis': ['Lumbar puncture (CSF analysis)', 'Blood culture', 'CT scan brain (if focal neurology)', 'Full Blood Count', 'CRP'],
  'Dengue Fever': ['NS1 antigen test', 'Dengue IgM / IgG antibody', 'Full Blood Count (platelet count)', 'Liver function tests'],
  'Sickle Cell Crisis': ['Haemoglobin electrophoresis', 'Full Blood Count', 'Peripheral blood film', 'Sickle solubility test'],
  'Iron Deficiency Anemia': ['Full Blood Count (FBC)', 'Serum ferritin', 'Serum iron & TIBC', 'Peripheral blood film'],
  'Cystitis UTI': ['Urine dipstick', 'Urine microscopy, culture & sensitivity (MCS)', 'Full Blood Count'],
  'Gastroenteritis': ['Stool microscopy & culture', 'Electrolytes', 'Full Blood Count', 'Urea and creatinine'],
  'Asthma': ['Peak expiratory flow rate (PEFR)', 'Spirometry', 'Chest X-ray', 'Allergy skin prick test', 'Total IgE'],
  'Peptic Ulcer': ['H. pylori stool antigen / breath test', 'Upper GI endoscopy', 'Stool occult blood test', 'Full Blood Count'],
  'Chickenpox': ['Clinical diagnosis (usually sufficient)', 'Varicella-zoster IgM / IgG (if uncertain)', 'Full Blood Count'],
  'Measles': ['Clinical diagnosis', 'Measles IgM antibody test', 'Throat swab PCR'],
  'COVID-19': ['SARS-CoV-2 rapid antigen test', 'RT-PCR nasal/throat swab', 'Chest X-ray or HRCT', 'SpO2 pulse oximetry', 'Full Blood Count'],
  'Sepsis': ['Blood culture (×2)', 'Full Blood Count', 'CRP / Procalcitonin', 'Lactate', 'Renal & liver function tests'],
  'Stroke': ['CT scan brain', 'MRI brain', 'Blood glucose', 'Full Blood Count', 'ECG', 'Carotid ultrasound'],
  'Heart Failure': ['Echocardiogram', 'ECG', 'Chest X-ray', 'BNP / NT-proBNP', 'Full Blood Count', 'Renal function'],
  'Schistosomiasis': ['Stool/urine microscopy (ova)', 'Schistosoma serology (ELISA)', 'Full Blood Count', 'Renal/liver function tests'],
  'Onchocerciasis': ['Skin snip microscopy', 'Mazzotti test', 'Slit-lamp eye exam'],
  'Filariasis': ['Night blood film (microfilariae)', 'Antigen detection test (ICT card)', 'Ultrasound (filarial dance sign)'],
};

const PredictionResults = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useAuth();

  const symptoms = location.state?.symptoms || [];
  const duration = location.state?.duration || 'Not specified';
  const severity = location.state?.severity || 'Not specified';
  const gender = location.state?.gender || 'Not specified';
  const age = location.state?.age || 'Not specified';
  const isPregnant = location.state?.isPregnant || false;
  const pregnancyWeeks = location.state?.pregnancyWeeks || 'Not specified';
  const predictions = location.state?.predictions || [];
  const analysisNote = location.state?.analysisNote || null;
  const apiDisclaimer = location.state?.disclaimer || null;
  const pregnancyNote = location.state?.pregnancyNote || null;
  const fatigueNote = location.state?.fatigueNote || null;
  const fatigueContext = location.state?.fatigueContext || false;
  const predictionLogId = location.state?.predictionLogId || null;

  const [expandedId, setExpandedId] = useState(predictions[0]?.id || null);
  const [showAllConditions, setShowAllConditions] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [actualDiagnosis, setActualDiagnosis] = useState('');
  const [feedbackComment, setFeedbackComment] = useState('');

  const buildReadAloudText = () => {
    const top = predictions[0];
    if (!top) return '';
    const lines = [
      `Diagnosis Assessment.`,
      symptoms.length ? `You reported ${symptoms.length} symptom${symptoms.length !== 1 ? 's' : ''}: ${symptoms.join(', ')}.` : '',
      `The top match is ${top.name} with ${top.confidence} percent confidence.`,
      top.description ? top.description : '',
      top.whenToSeeDoctorText ? `When to seek care: ${top.whenToSeeDoctorText}` : '',
      top.treatment ? `Treatment: ${top.treatment}` : '',
      predictions.length > 1
        ? `Other possible conditions include: ${predictions.slice(1, 4).map(p => p.name).join(', ')}.`
        : '',
      `This is not a medical diagnosis. Always consult a qualified health professional.`,
    ];
    return lines.filter(Boolean).join(' ');
  };

  useEffect(() => {
    if (symptoms.length === 0 || predictions.length === 0) {
      navigate('/symptom-checker');
    }
  }, [symptoms, predictions, navigate]);

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const handleSaveDiagnosis = () => {
    if (!user) {
      toast({ title: 'Authentication Required', description: 'Please login to save this diagnosis to your profile.' });
      navigate('/login', { state: { from: location } });
      return;
    }
    const checkRecord = {
      id: 'diagnosis_' + Date.now(),
      user_id: user.id,
      symptoms,
      duration,
      severity,
      gender,
      age,
      isPregnant,
      pregnancyWeeks,
      results: predictions,
      created_at: new Date().toISOString(),
    };
    const existing = JSON.parse(localStorage.getItem(`symptom_checks_${user.id}`) || '[]');
    localStorage.setItem(`symptom_checks_${user.id}`, JSON.stringify([checkRecord, ...existing]));
    toast({ title: 'Diagnosis Saved', description: 'Results successfully added to your health history.' });
  };

  const handleFeedback = async (wasHelpful) => {
    setFeedbackLoading(true);
    try {
      await submitFeedback({
        prediction_log_id: predictionLogId,
        top_predicted: predictions[0]?.name || predictions[0]?.disease || 'Unknown',
        was_helpful: wasHelpful,
        confirmed_disease: actualDiagnosis.trim() || null,
        comment: feedbackComment.trim() || null,
      });
      setFeedbackSubmitted(true);
      toast({ title: 'Thank you!', description: 'Your feedback helps improve MediGuard for the Bamenda community.' });
    } catch {
      toast({ title: 'Feedback not saved', description: 'Please try again.', variant: 'destructive' });
    } finally {
      setFeedbackLoading(false);
    }
  };

  const getUrgencyColor = (urgency) => {
    switch (urgency?.toLowerCase()) {
      case 'red': return 'bg-red-500 text-white';
      case 'yellow': return 'bg-yellow-500 text-white';
      case 'green': return 'bg-emerald-500 text-white';
      default: return 'bg-primary text-primary-foreground';
    }
  };

  const getConfidenceBadgeColor = (confidence) => {
    if (confidence >= 70) return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300';
    if (confidence >= 40) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300';
    return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
  };

  const handlePrint = () => {
    const top = predictions[0];
    const tests = DISEASE_TESTS[top?.name] || DISEASE_TESTS[top?.disease] || [];
    const testRows = tests.map(t => `<li style="margin:4px 0;">&#x2022; ${t}</li>`).join('');
    const symptomList = symptoms.map(s => `<span style="display:inline-block;background:#e8f4ff;border:1px solid #b3d7ff;border-radius:4px;padding:2px 8px;margin:2px;font-size:13px;">${s}</span>`).join(' ');
    const allPreds = predictions.slice(0, 5).map((p, i) =>
      `<tr style="background:${i % 2 === 0 ? '#f9f9f9' : '#fff'}">
        <td style="padding:6px 10px;border:1px solid #ddd;">${i + 1}. ${p.name || p.disease}</td>
        <td style="padding:6px 10px;border:1px solid #ddd;text-align:center;">${p.confidence}%</td>
        <td style="padding:6px 10px;border:1px solid #ddd;">${p.severity || '—'}</td>
      </tr>`
    ).join('');
    const html = `<!DOCTYPE html><html><head><title>MediGuard Diagnosis – ${top?.name || 'Results'}</title>
    <style>body{font-family:Arial,sans-serif;margin:32px;color:#1a1a1a;max-width:800px}
    h1{color:#2563eb;border-bottom:2px solid #2563eb;padding-bottom:8px}
    h2{color:#374151;margin-top:24px;font-size:16px}
    table{border-collapse:collapse;width:100%;margin-top:8px}
    th{background:#2563eb;color:#fff;padding:8px 10px;text-align:left;border:1px solid #1d4ed8}
    .footer{margin-top:32px;padding:12px;background:#fef3c7;border:1px solid #fcd34d;border-radius:6px;font-size:12px}
    @media print{body{margin:16px}.no-print{display:none}}</style></head>
    <body>
    <h1>MediGuard – Diagnosis Assessment</h1>
    <p><strong>Date:</strong> ${new Date().toLocaleDateString('en-GB', { day:'numeric', month:'long', year:'numeric' })}</p>
    ${gender !== 'Not specified' ? `<p><strong>Patient:</strong> ${gender}${age !== 'Not specified' ? `, Age ${age}` : ''}${isPregnant ? ', Pregnant' : ''}</p>` : ''}
    <h2>Reported Symptoms</h2><div>${symptomList}</div>
    ${duration !== 'Not specified' ? `<p><strong>Duration:</strong> ${duration} &nbsp;|&nbsp; <strong>Severity:</strong> ${severity}</p>` : ''}
    <h2>Top Predictions</h2>
    <table><tr><th>Condition</th><th>Confidence</th><th>Severity</th></tr>${allPreds}</table>
    ${tests.length > 0 ? `<h2>Recommended Laboratory Tests (for ${top?.name || 'top condition'})</h2><ul style="margin:0;padding-left:16px">${testRows}</ul><p style="font-size:12px;color:#555;">Present this list to your doctor or laboratory for confirmation.</p>` : ''}
    ${top?.treatment ? `<h2>Treatment Note</h2><p>${top.treatment}</p>` : ''}
    <div class="footer"><strong>IMPORTANT:</strong> This is an AI-generated symptom assessment, NOT a medical diagnosis. Always consult a qualified health professional before starting any treatment. For emergencies, go to Bamenda Regional Hospital immediately.</div>
    </body></html>`;
    const w = window.open('', '_blank');
    if (!w) { toast({ title: 'Popup blocked', description: 'Allow popups for this site to generate the PDF.', variant: 'destructive' }); return; }
    w.document.write(html);
    w.document.close();
    w.focus();
    setTimeout(() => { w.print(); }, 600);
  };

  const containerVariants = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.1 } } };
  const itemVariants = { hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { duration: 0.4 } } };

  const displayedPredictions = showAllConditions ? predictions : predictions.slice(0, 3);

  return (
    <>
      <Helmet>
        <title>Diagnosis Results - MediGuard Bamenda</title>
        <meta name="description" content="Comprehensive health diagnosis results and medical guidance." />
      </Helmet>

      <div className="min-h-screen bg-muted/30 py-8 md:py-12">
        <motion.div className="container mx-auto px-4 max-w-4xl" variants={containerVariants} initial="hidden" animate="visible">

          {/* Header Controls */}
          <div className="flex flex-wrap justify-between items-center mb-8 gap-3">
            <Button variant="outline" onClick={() => navigate('/symptom-checker')} className="hover:bg-muted">
              <ArrowLeft className="mr-2 h-4 w-4" />New Diagnosis
            </Button>
            <div className="flex gap-2 flex-wrap">
              <SpeakButton text={buildReadAloudText()} label="Read Aloud" size="md" />
              <Button variant="outline" onClick={handlePrint} className="shadow-sm">
                <Printer className="mr-2 h-4 w-4" />Download PDF
              </Button>
              <Button onClick={handleSaveDiagnosis} variant="default" className="shadow-md">
                <Save className="mr-2 h-4 w-4" />{user ? 'Save Diagnosis' : 'Login to Save'}
              </Button>
            </div>
          </div>

          {/* Context Summary */}
          <motion.div variants={itemVariants} className="mb-10 text-center">
            <div className="inline-flex items-center justify-center p-3 bg-primary/10 rounded-full mb-4">
              <Activity className="h-8 w-8 text-primary" />
            </div>
            <h1 className="text-3xl md:text-4xl font-bold mb-4 text-foreground">Diagnosis Assessment</h1>

            <div className="flex flex-wrap justify-center gap-3 mb-4">
              {gender !== 'Not specified' && (
                <Badge variant="outline" className="bg-background px-3 py-1"><User className="h-3 w-3 mr-1" />{gender}</Badge>
              )}
              {age !== 'Not specified' && (
                <Badge variant="outline" className="bg-background px-3 py-1"><Clock className="h-3 w-3 mr-1" />{age} years</Badge>
              )}
              {isPregnant && (
                <Badge variant="outline" className="bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-300 border-pink-200">
                  <Baby className="h-3 w-3 mr-1" />Pregnant{pregnancyWeeks !== 'Not specified' ? ` - ${pregnancyWeeks} weeks` : ''}
                </Badge>
              )}
              {duration !== 'Not specified' && (
                <Badge variant="outline" className="bg-background px-3 py-1"><Clock className="h-3 w-3 mr-1" />{duration}</Badge>
              )}
              {severity !== 'Not specified' && (
                <Badge variant="outline" className="bg-background px-3 py-1"><Activity className="h-3 w-3 mr-1" />{severity} severity</Badge>
              )}
              {fatigueContext && (
                <Badge variant="outline" className="bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300 border-amber-200">
                  <Brain className="h-3 w-3 mr-1" />Fatigue context
                </Badge>
              )}
            </div>

            <p className="text-muted-foreground max-w-2xl mx-auto">
              Based on your reported {symptoms.length} symptom{symptoms.length !== 1 ? 's' : ''}, our AI identified the following potential conditions.
            </p>

            <div className="flex flex-wrap justify-center gap-2 mt-4">
              {symptoms.map(s => (
                <Badge key={s} variant="outline" className="bg-background text-foreground border text-sm py-1">{s}</Badge>
              ))}
            </div>

            {analysisNote && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                className="mt-4 p-4 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800 flex items-start gap-3 text-left">
                <HelpCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-blue-800 dark:text-blue-300">{analysisNote}</p>
              </motion.div>
            )}
          </motion.div>

          <motion.div variants={itemVariants} className="mb-6">
            <DisclaimerBanner variant="warning" />
            {apiDisclaimer && <p className="text-xs text-muted-foreground mt-2 text-center">{apiDisclaimer}</p>}
          </motion.div>

          {/* Results Summary */}
          <motion.div variants={itemVariants} className="mb-6 grid grid-cols-3 gap-2 sm:gap-4">
            <Card className="bg-gradient-to-br from-primary/5 to-transparent">
              <CardContent className="p-2.5 sm:p-4 text-center min-h-[86px] sm:min-h-0 flex flex-col justify-center">
                <div className="text-lg sm:text-2xl font-bold text-primary">{predictions.length}</div>
                <p className="text-[10px] sm:text-sm text-muted-foreground leading-tight">Possible Conditions</p>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-yellow-500/5 to-transparent">
              <CardContent className="p-2.5 sm:p-4 text-center min-h-[86px] sm:min-h-0 flex flex-col justify-center">
                <div className="text-lg sm:text-2xl font-bold text-yellow-600">
                  {predictions.filter(p => p.severity === 'High').length}
                </div>
                <p className="text-[10px] sm:text-sm text-muted-foreground leading-tight">High Severity</p>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-green-500/5 to-transparent">
              <CardContent className="p-2.5 sm:p-4 text-center min-h-[86px] sm:min-h-0 flex flex-col justify-center">
                <div className="text-lg sm:text-2xl font-bold text-green-600">
                  {Math.max(...predictions.map(p => p.confidence))}%
                </div>
                <p className="text-[10px] sm:text-sm text-muted-foreground leading-tight">Top Match</p>
              </CardContent>
            </Card>
          </motion.div>

          {/* Top Predictions List */}
          <div className="space-y-6">
            {displayedPredictions.map((disease, index) => {
              const isExpanded = expandedId === disease.id;
              const isTop = index === 0;
              const confidenceLevel = disease.confidence >= 70 ? 'High' : disease.confidence >= 40 ? 'Medium' : 'Low';
              const matchedSymptoms = disease.matched_symptoms || [];
              const causes = disease.causes || '';
              const treatment = disease.treatment || '';
              const prevention = Array.isArray(disease.prevention) ? disease.prevention : [];

              return (
                <motion.div key={disease.id} variants={itemVariants}>
                  <Card className={`overflow-hidden transition-all duration-300 border-2 ${isTop ? 'border-primary shadow-lg' : 'border-border shadow-sm'}`}>

                    {/* Card Header */}
                    <div
                      className={`p-5 md:p-6 cursor-pointer flex flex-col md:flex-row gap-4 items-start md:items-center justify-between ${isTop ? 'bg-primary/5' : 'bg-card hover:bg-muted/30'}`}
                      onClick={() => toggleExpand(disease.id)}
                    >
                      <div className="flex-1 w-full">
                        <div className="flex items-center gap-2 mb-2 flex-wrap">
                          {isTop && <Badge className="bg-primary hover:bg-primary text-xs">Top Match</Badge>}
                          <Badge className={getConfidenceBadgeColor(disease.confidence)}>{confidenceLevel} Confidence</Badge>
                          {disease.severity === 'High' && (
                            <Badge variant="destructive" className="text-xs"><ShieldAlert className="h-3 w-3 mr-1" />Urgent</Badge>
                          )}
                          {isPregnant && disease.pregnancySafe === false && (
                            <Badge variant="destructive" className="text-xs"><AlertTriangle className="h-3 w-3 mr-1" />Pregnancy Warning</Badge>
                          )}
                        </div>
                        <h2 className="text-xl md:text-2xl font-bold text-foreground">{disease.name}</h2>
                        {getCommonName(disease.name) && (
                          <p className="text-sm text-primary font-medium -mt-1">
                            Also known as: {getCommonName(disease.name)}
                          </p>
                        )}
                        <p className="text-sm text-muted-foreground line-clamp-2 md:line-clamp-1 mt-1">{disease.description}</p>

                        {/* Matched symptoms explainability */}
                        {matchedSymptoms.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            <span className="text-xs text-muted-foreground mr-1">Matched:</span>
                            {matchedSymptoms.map(s => (
                              <Badge key={s} variant="outline" className="text-xs bg-green-50 border-green-200 text-green-700 dark:bg-green-900/20 dark:text-green-400">
                                <CheckCircle2 className="h-2.5 w-2.5 mr-1" />{s}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Confidence Bar */}
                      <div className="w-full md:w-48 flex flex-col gap-1 shrink-0">
                        <div className="flex justify-between text-sm font-semibold">
                          <span>Match</span>
                          <span className={isTop ? 'text-primary' : 'text-foreground'}>{disease.confidence}%</span>
                        </div>
                        <div className="h-2.5 w-full bg-muted rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-1000 ease-out ${disease.confidence >= 70 ? 'bg-green-500' : disease.confidence >= 40 ? 'bg-yellow-500' : 'bg-gray-400'}`}
                            style={{ width: `${disease.confidence}%` }}
                          />
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {matchedSymptoms.length > 0 ? matchedSymptoms.length : (disease.matchCount || 0)} of {disease.symptoms?.length || 0} symptoms match
                        </p>
                      </div>

                      <div className="hidden md:flex items-center justify-center shrink-0">
                        <ChevronDown className={`h-6 w-6 text-muted-foreground transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`} />
                      </div>
                    </div>

                    {/* Expandable Content */}
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.3 }}
                        >
                          <div className="border-t border-border p-5 md:p-6 bg-card space-y-6">

                            {/* Pregnancy Warning */}
                            {isPregnant && disease.pregnancyWarning && (
                              <div className="p-4 bg-orange-50 dark:bg-orange-950/30 rounded-lg border border-orange-200 dark:border-orange-800 flex items-start gap-3">
                                <AlertTriangle className="h-5 w-5 text-orange-600 dark:text-orange-400 mt-0.5" />
                                <div>
                                  <h4 className="font-bold text-orange-800 dark:text-orange-300 mb-1">Pregnancy Consideration</h4>
                                  <p className="text-sm text-orange-700 dark:text-orange-400">{disease.pregnancyWarning}</p>
                                </div>
                              </div>
                            )}

                            {/* When to see doctor */}
                            <div className={`p-4 rounded-lg flex items-start gap-3 ${disease.whenToSeeDoctorUrgency === 'red' ? 'bg-red-50 dark:bg-red-900/20 border border-red-200' : 'bg-muted border'}`}>
                              <Clock className={`h-6 w-6 mt-0.5 shrink-0 ${disease.whenToSeeDoctorUrgency === 'red' ? 'text-red-600' : 'text-foreground'}`} />
                              <div>
                                <h4 className="font-bold text-base mb-1 flex items-center gap-2 flex-wrap">
                                  When to Seek Medical Care
                                  <Badge className={getUrgencyColor(disease.whenToSeeDoctorUrgency)}>
                                    {disease.whenToSeeDoctorUrgency === 'red' ? 'Seek Care Immediately' : disease.whenToSeeDoctorUrgency === 'yellow' ? 'See Doctor Soon' : 'Routine Care'}
                                  </Badge>
                                </h4>
                                <p className="text-sm text-foreground/80">{disease.whenToSeeDoctorText}</p>
                              </div>
                            </div>

                            {/* Causes + Treatment (from DB) */}
                            <div className="grid md:grid-cols-2 gap-6">
                              {causes && (
                                <div>
                                  <h4 className="font-bold flex items-center gap-2 mb-3 border-b pb-2">
                                    <Microscope className="h-5 w-5 text-blue-600" />Causes
                                  </h4>
                                  <p className="text-sm text-foreground/90 leading-relaxed">{causes}</p>
                                </div>
                              )}
                              {treatment && (
                                <div>
                                  <h4 className="font-bold flex items-center gap-2 mb-3 border-b pb-2">
                                    <Pill className="h-5 w-5 text-primary" />Treatment
                                  </h4>
                                  <p className="text-sm text-foreground/90 leading-relaxed">{treatment}</p>
                                </div>
                              )}
                            </div>

                            {/* Recommended Tests */}
                            {(() => {
                              const tests = DISEASE_TESTS[disease.name] || DISEASE_TESTS[disease.disease] || [];
                              return tests.length > 0 ? (
                                <motion.div
                                  initial={{ opacity: 0, y: 8 }}
                                  animate={{ opacity: 1, y: 0 }}
                                  className="p-4 rounded-lg border border-purple-200 bg-purple-50 dark:bg-purple-950/20 dark:border-purple-800"
                                >
                                  <h4 className="font-bold flex items-center gap-2 mb-2 text-purple-800 dark:text-purple-300">
                                    <FlaskConical className="h-4 w-4" />Recommended Tests at the Hospital
                                  </h4>
                                  <p className="text-xs text-purple-600 dark:text-purple-400 mb-3">
                                    Show this list to your doctor or lab technician for confirmation:
                                  </p>
                                  <div className="flex flex-wrap gap-2">
                                    {tests.map((test, i) => (
                                      <Badge key={i} variant="outline" className="bg-white dark:bg-purple-900/30 border-purple-300 text-purple-800 dark:text-purple-300 text-xs">
                                        <Microscope className="h-2.5 w-2.5 mr-1" />{test}
                                      </Badge>
                                    ))}
                                  </div>
                                </motion.div>
                              ) : null;
                            })()}

                            {/* Prevention */}
                            {prevention.length > 0 && (
                              <div>
                                <h4 className="font-bold flex items-center gap-2 mb-3 border-b pb-2">
                                  <Shield className="h-5 w-5 text-green-600" />Prevention
                                </h4>
                                <ul className="space-y-1.5">
                                  {prevention.map((tip, i) => (
                                    <li key={i} className="flex items-start gap-2 text-sm text-foreground/90">
                                      <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                                      <span>{tip}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            <div className="grid md:grid-cols-2 gap-8">
                              <div className="space-y-6">
                                {disease.firstAidSteps && disease.firstAidSteps.length > 0 && (
                                  <div>
                                    <h4 className="font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-2 mb-3 border-b pb-2">
                                      <HeartPulse className="h-5 w-5" />First Aid Steps
                                    </h4>
                                    <ol className="list-decimal list-outside ml-4 space-y-2 text-sm text-foreground/90">
                                      {disease.firstAidSteps.map((step, i) => <li key={i} className="pl-1">{step}</li>)}
                                    </ol>
                                  </div>
                                )}
                                {disease.homeCareTips && disease.homeCareTips.length > 0 && (
                                  <div>
                                    <h4 className="font-bold flex items-center gap-2 mb-3 border-b pb-2">
                                      <CheckCircle2 className="h-5 w-5 text-primary" />Home Care Recommendations
                                    </h4>
                                    <ul className="space-y-2 text-sm text-foreground/90">
                                      {disease.homeCareTips.map((tip, i) => (
                                        <li key={i} className="flex items-start gap-2">
                                          <span className="text-primary font-bold mt-0.5">•</span><span>{tip}</span>
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                              <div className="space-y-6">
                                {disease.emergencySigns && disease.emergencySigns.length > 0 && (
                                  <div className="bg-destructive/10 p-4 rounded-lg border border-destructive/20">
                                    <h4 className="font-bold text-destructive flex items-center gap-2 mb-2">
                                      <AlertCircle className="h-5 w-5" />Warning Signs
                                    </h4>
                                    <p className="text-xs text-destructive mb-2 font-medium">Go to ER if you experience:</p>
                                    <ul className="space-y-1 text-sm text-foreground/90">
                                      {disease.emergencySigns.map((sign, i) => (
                                        <li key={i} className="flex items-start gap-2">
                                          <span className="text-destructive font-bold mt-0.5">!</span><span>{sign}</span>
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                                {disease.medicationsToAvoid && disease.medicationsToAvoid.length > 0 && (
                                  <div>
                                    <h4 className="font-bold flex items-center gap-2 mb-3 border-b pb-2 text-orange-600 dark:text-orange-400">
                                      <Pill className="h-5 w-5" />Medications to Avoid
                                    </h4>
                                    <div className="flex flex-wrap gap-2">
                                      {disease.medicationsToAvoid.map((med, i) => (
                                        <Badge key={i} variant="outline" className="border-orange-200 bg-orange-50 text-orange-800 dark:bg-orange-950/30 dark:text-orange-300">{med}</Badge>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Action Links */}
                            <div className="flex flex-wrap gap-3 pt-4 border-t border-border">
                              <Link to={`/disease/${disease.id}`} className="flex-1 sm:flex-none">
                                <Button variant="outline" className="w-full"><Info className="mr-2 h-4 w-4" />Full Disease Info</Button>
                              </Link>
                              <Button
                                className="flex-1 sm:flex-none bg-secondary hover:bg-secondary/90 text-white"
                                onClick={() => navigate('/chat-ai', {
                                  state: { initialMessage: `I received a diagnosis assessment suggesting ${disease.name} as a match. ${isPregnant ? 'I am pregnant. ' : ''}Can you explain home care steps and tell me more?` }
                                })}
                              >
                                <MessageCircle className="mr-2 h-4 w-4" />Discuss with AI
                              </Button>
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </Card>
                </motion.div>
              );
            })}
          </div>

          {/* Show More/Less */}
          {predictions.length > 3 && (
            <motion.div variants={itemVariants} className="text-center mt-6">
              <Button variant="outline" onClick={() => setShowAllConditions(!showAllConditions)} className="px-8">
                {showAllConditions ? 'Show Less' : `Show ${predictions.length - 3} More Conditions`}
              </Button>
            </motion.div>
          )}

          {/* Low Confidence Note */}
          {predictions.length > 0 && predictions[0].confidence < 40 && (
            <motion.div variants={itemVariants} className="mt-8 p-5 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800">
              <div className="flex items-start gap-3">
                <Brain className="h-6 w-6 text-blue-600 dark:text-blue-400 mt-0.5" />
                <div>
                  <h3 className="font-bold text-blue-800 dark:text-blue-300 mb-2">Low Confidence Analysis</h3>
                  <p className="text-sm text-blue-700 dark:text-blue-400">
                    Matches have lower confidence. Try adding more symptoms, or consult a health professional in Bamenda for a full assessment.
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {/* Pregnancy & fatigue context notes — shown at bottom after results */}
          {(pregnancyNote || fatigueNote) && (
            <motion.div variants={itemVariants} className="mt-8 space-y-3">
              {pregnancyNote && (
                <div className="p-4 bg-pink-50 dark:bg-pink-950/30 rounded-xl border border-pink-200 dark:border-pink-800 flex items-start gap-3">
                  <Baby className="h-5 w-5 text-pink-600 dark:text-pink-400 mt-0.5 shrink-0" />
                  <p className="text-sm text-pink-800 dark:text-pink-300">{pregnancyNote}</p>
                </div>
              )}
              {fatigueNote && (
                <div className="p-4 bg-amber-50 dark:bg-amber-950/30 rounded-xl border border-amber-200 dark:border-amber-800 flex items-start gap-3">
                  <Brain className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
                  <p className="text-sm text-amber-800 dark:text-amber-300">{fatigueNote}</p>
                </div>
              )}
            </motion.div>
          )}

          {/* Bamenda Health Facilities */}
          <motion.div variants={itemVariants} className="mt-10">
            <NearbyFacilities />
          </motion.div>

          {/* Feedback Section */}
          <motion.div variants={itemVariants} className="mt-8">
            <Card className="border-primary/20">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Heart className="h-5 w-5 text-primary" />Help Improve MediGuard
                </CardTitle>
                <CardDescription>
                  After visiting a health professional, let us know if the assessment was accurate. Your feedback improves accuracy for the entire Bamenda community.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {feedbackSubmitted ? (
                  <div className="flex items-center gap-3 text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-950/30 p-4 rounded-lg">
                    <CheckCircle2 className="h-5 w-5 shrink-0" />
                    <p className="text-sm font-medium">Feedback recorded. Thank you for helping improve MediGuard for Bamenda!</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium text-foreground mb-1 block">
                        Actual diagnosis (optional — what did the doctor say?)
                      </label>
                      <input
                        type="text"
                        value={actualDiagnosis}
                        onChange={(e) => setActualDiagnosis(e.target.value)}
                        placeholder="e.g. Malaria, Typhoid Fever…"
                        className="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/40"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium text-foreground mb-1 block">
                        Comment (optional)
                      </label>
                      <textarea
                        value={feedbackComment}
                        onChange={(e) => setFeedbackComment(e.target.value)}
                        placeholder="Any additional feedback…"
                        rows={2}
                        className="w-full px-3 py-2 text-sm border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/40 resize-none"
                      />
                    </div>
                    <div className="flex gap-3">
                      <Button
                        variant="outline"
                        className="flex-1 border-green-300 text-green-700 hover:bg-green-50"
                        onClick={() => handleFeedback(true)}
                        disabled={feedbackLoading}
                      >
                        <ThumbsUp className="mr-2 h-4 w-4" />Yes, it was helpful
                      </Button>
                      <Button
                        variant="outline"
                        className="flex-1 border-red-300 text-red-700 hover:bg-red-50"
                        onClick={() => handleFeedback(false)}
                        disabled={feedbackLoading}
                      >
                        <ThumbsDown className="mr-2 h-4 w-4" />Not helpful
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Footer Disclaimer */}
          <motion.div variants={itemVariants} className="text-center text-sm text-muted-foreground mt-10 pb-8 p-4 bg-muted/50 rounded-lg">
            <Stethoscope className="h-8 w-8 mx-auto mb-2 text-muted-foreground/50" />
            <p className="font-semibold text-foreground mb-1">Medical Disclaimer</p>
            <p>
              These results are generated by an AI algorithm matching your symptoms against a database.
              <strong> This is NOT a medical diagnosis.</strong> Do not disregard professional medical advice
              or delay seeking it because of information provided here.
            </p>
          </motion.div>

        </motion.div>
      </div>
    </>
  );
};

export default PredictionResults;
