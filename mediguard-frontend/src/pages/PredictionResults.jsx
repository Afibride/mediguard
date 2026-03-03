import React, { useEffect, useState } from 'react';
import { Helmet } from 'react-helmet';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, ArrowLeft, MessageCircle, RefreshCw, Info, HeartPulse, Activity, Stethoscope, Clock, ShieldAlert, Save, Brain, ChevronDown, CheckCircle2, Pill, AlertTriangle, Baby, User, Heart, HelpCircle, Thermometer, Scale } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/components/AuthContext';

const PredictionResults = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useAuth();
  
  // Enhanced data structure from SymptomChecker
  const symptoms = location.state?.symptoms || [];
  const duration = location.state?.duration || 'Not specified';
  const severity = location.state?.severity || 'Not specified';
  const gender = location.state?.gender || 'Not specified';
  const age = location.state?.age || 'Not specified';
  const isPregnant = location.state?.isPregnant || false;
  const predictions = location.state?.predictions || [];
  const analysisNote = location.state?.analysisNote || null;
  
  const [expandedId, setExpandedId] = useState(predictions[0]?.id || null);
  const [showAllConditions, setShowAllConditions] = useState(false);

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
      toast({
        title: "Authentication Required",
        description: "Please login to save this diagnosis to your profile.",
      });
      navigate('/login', { state: { from: location } });
      return;
    }

    const checkRecord = {
      id: 'diagnosis_' + Date.now(),
      user_id: user.id,
      symptoms: symptoms,
      duration: duration,
      severity: severity,
      gender: gender,
      age: age,
      isPregnant: isPregnant,
      results: predictions,
      created_at: new Date().toISOString()
    };
    
    const existing = JSON.parse(localStorage.getItem(`symptom_checks_${user.id}`) || '[]');
    localStorage.setItem(`symptom_checks_${user.id}`, JSON.stringify([checkRecord, ...existing]));

    toast({
      title: "Diagnosis Saved",
      description: "Results successfully added to your health history.",
    });
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

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.4 } }
  };

  const displayedPredictions = showAllConditions ? predictions : predictions.slice(0, 3);

  return (
    <>
      <Helmet>
        <title>Diagnosis Results - MediGuard Bamenda</title>
        <meta name="description" content="Comprehensive health diagnosis results and medical guidance." />
      </Helmet>

      <div className="min-h-screen bg-muted/30 py-8 md:py-12">
        <motion.div 
          className="container mx-auto px-4 max-w-4xl"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Header Controls */}
          <div className="flex flex-wrap justify-between items-center mb-8 gap-4">
            <Button variant="outline" onClick={() => navigate('/symptom-checker')} className="hover:bg-muted">
              <ArrowLeft className="mr-2 h-4 w-4" />
              New Diagnosis
            </Button>
            
            <Button onClick={handleSaveDiagnosis} variant="default" className="shadow-md">
              <Save className="mr-2 h-4 w-4" />
              {user ? 'Save Diagnosis' : 'Login to Save'}
            </Button>
          </div>

          {/* Context Summary */}
          <motion.div variants={itemVariants} className="mb-10 text-center">
            <div className="inline-flex items-center justify-center p-3 bg-primary/10 rounded-full mb-4">
              <Activity className="h-8 w-8 text-primary" />
            </div>
            <h1 className="text-3xl md:text-4xl font-bold mb-4 text-foreground">Diagnosis Assessment</h1>
            
            {/* Patient Profile Summary */}
            <div className="flex flex-wrap justify-center gap-3 mb-4">
              {gender !== 'Not specified' && (
                <Badge variant="outline" className="bg-background px-3 py-1">
                  <User className="h-3 w-3 mr-1" /> {gender}
                </Badge>
              )}
              {age !== 'Not specified' && (
                <Badge variant="outline" className="bg-background px-3 py-1">
                  <Clock className="h-3 w-3 mr-1" /> {age} years
                </Badge>
              )}
              {isPregnant && (
                <Badge variant="outline" className="bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-300 border-pink-200">
                  <Baby className="h-3 w-3 mr-1" /> Pregnant
                </Badge>
              )}
              {duration !== 'Not specified' && (
                <Badge variant="outline" className="bg-background px-3 py-1">
                  <Clock className="h-3 w-3 mr-1" /> {duration}
                </Badge>
              )}
              {severity !== 'Not specified' && (
                <Badge variant="outline" className="bg-background px-3 py-1">
                  <Activity className="h-3 w-3 mr-1" /> {severity} severity
                </Badge>
              )}
            </div>

            <p className="text-muted-foreground max-w-2xl mx-auto">
              Based on your reported {symptoms.length} symptom{symptoms.length !== 1 ? 's' : ''}, our AI has identified the following potential conditions.
            </p>
            
            {/* Selected Symptoms */}
            <div className="flex flex-wrap justify-center gap-2 mt-4">
              {symptoms.map(s => (
                <Badge key={s} variant="secondary" className="bg-background border text-sm py-1">
                  {s}
                </Badge>
              ))}
            </div>

            {/* Single Symptom Note */}
            {analysisNote && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 p-4 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800 flex items-start gap-3 text-left"
              >
                <HelpCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-blue-800 dark:text-blue-300">{analysisNote}</p>
              </motion.div>
            )}
          </motion.div>

          {/* Results Summary */}
          <motion.div variants={itemVariants} className="mb-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="bg-gradient-to-br from-primary/5 to-transparent">
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-primary">{predictions.length}</div>
                <p className="text-sm text-muted-foreground">Possible Conditions</p>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-yellow-500/5 to-transparent">
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {predictions.filter(p => p.severity === 'High').length}
                </div>
                <p className="text-sm text-muted-foreground">High Severity</p>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-green-500/5 to-transparent">
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-green-600">
                  {Math.max(...predictions.map(p => p.confidence))}%
                </div>
                <p className="text-sm text-muted-foreground">Top Match</p>
              </CardContent>
            </Card>
          </motion.div>

          {/* Top Predictions List */}
          <div className="space-y-6">
            {displayedPredictions.map((disease, index) => {
              const isExpanded = expandedId === disease.id;
              const isTop = index === 0;
              const confidenceLevel = disease.confidence >= 70 ? 'High' : disease.confidence >= 40 ? 'Medium' : 'Low';

              return (
                <motion.div key={disease.id} variants={itemVariants}>
                  <Card className={`overflow-hidden transition-all duration-300 border-2 ${
                    isTop ? 'border-primary shadow-lg' : 'border-border shadow-sm'
                  }`}>
                    
                    {/* Card Header (Clickable) */}
                    <div 
                      className={`p-5 md:p-6 cursor-pointer flex flex-col md:flex-row gap-4 items-start md:items-center justify-between ${
                        isTop ? 'bg-primary/5' : 'bg-card hover:bg-muted/30'
                      }`}
                      onClick={() => toggleExpand(disease.id)}
                    >
                      <div className="flex-1 w-full">
                        <div className="flex items-center gap-2 mb-2 flex-wrap">
                          {isTop && (
                            <Badge className="bg-primary hover:bg-primary text-xs">Top Match</Badge>
                          )}
                          <Badge className={getConfidenceBadgeColor(disease.confidence)}>
                            {confidenceLevel} Confidence
                          </Badge>
                          {disease.severity === 'High' && (
                            <Badge variant="destructive" className="text-xs">
                              <ShieldAlert className="h-3 w-3 mr-1" /> Urgent
                            </Badge>
                          )}
                          {isPregnant && disease.pregnancySafe === false && (
                            <Badge variant="destructive" className="text-xs">
                              <AlertTriangle className="h-3 w-3 mr-1" /> Pregnancy Warning
                            </Badge>
                          )}
                        </div>
                        <h2 className="text-xl md:text-2xl font-bold text-foreground flex items-center gap-2">
                          {disease.name}
                        </h2>
                        <p className="text-sm text-muted-foreground line-clamp-2 md:line-clamp-1 mt-1">
                          {disease.description}
                        </p>
                      </div>

                      {/* Confidence Progress Bar */}
                      <div className="w-full md:w-48 flex flex-col gap-1 shrink-0">
                        <div className="flex justify-between text-sm font-semibold">
                          <span>Match</span>
                          <span className={isTop ? 'text-primary' : 'text-foreground'}>
                            {disease.confidence}%
                          </span>
                        </div>
                        <div className="h-2.5 w-full bg-muted rounded-full overflow-hidden">
                          <div 
                            className={`h-full rounded-full transition-all duration-1000 ease-out ${
                              disease.confidence >= 70 ? 'bg-green-500' :
                              disease.confidence >= 40 ? 'bg-yellow-500' : 'bg-gray-400'
                            }`}
                            style={{ width: `${disease.confidence}%` }}
                          />
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {disease.matchCount} of {disease.symptoms.length} symptoms match
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
                          <div className="border-t border-border p-5 md:p-6 bg-card space-y-8">
                            
                            {/* Pregnancy Warning (if applicable) */}
                            {isPregnant && disease.pregnancyWarning && (
                              <div className="p-4 bg-orange-50 dark:bg-orange-950/30 rounded-lg border border-orange-200 dark:border-orange-800 flex items-start gap-3">
                                <AlertTriangle className="h-5 w-5 text-orange-600 dark:text-orange-400 mt-0.5" />
                                <div>
                                  <h4 className="font-bold text-orange-800 dark:text-orange-300 mb-1">Pregnancy Consideration</h4>
                                  <p className="text-sm text-orange-700 dark:text-orange-400">{disease.pregnancyWarning}</p>
                                </div>
                              </div>
                            )}
                            
                            {/* Alert / When to see Doctor */}
                            <div className={`p-4 rounded-lg flex items-start gap-3 ${
                              disease.whenToSeeDoctorUrgency === 'red' 
                                ? 'bg-red-50 dark:bg-red-900/20 border border-red-200' 
                                : 'bg-muted border'
                            }`}>
                              <Clock className={`h-6 w-6 mt-0.5 shrink-0 ${
                                disease.whenToSeeDoctorUrgency === 'red' ? 'text-red-600' : 'text-foreground'
                              }`} />
                              <div>
                                <h4 className="font-bold text-base mb-1 flex items-center gap-2 flex-wrap">
                                  When to Seek Medical Care
                                  <Badge className={getUrgencyColor(disease.whenToSeeDoctorUrgency)}>
                                    {disease.whenToSeeDoctorUrgency === 'red' ? 'Seek Care Immediately' : 
                                     disease.whenToSeeDoctorUrgency === 'yellow' ? 'See Doctor Soon' : 
                                     'Routine Care'}
                                  </Badge>
                                </h4>
                                <p className="text-sm text-foreground/80">{disease.whenToSeeDoctorText}</p>
                              </div>
                            </div>

                            <div className="grid md:grid-cols-2 gap-8">
                              {/* Column 1 */}
                              <div className="space-y-8">
                                {/* First Aid */}
                                {disease.firstAidSteps && disease.firstAidSteps.length > 0 && (
                                  <div>
                                    <h4 className="font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-2 mb-3 border-b pb-2">
                                      <HeartPulse className="h-5 w-5" /> First Aid Steps
                                    </h4>
                                    <ol className="list-decimal list-outside ml-4 space-y-2 text-sm text-foreground/90">
                                      {disease.firstAidSteps.map((step, i) => (
                                        <li key={i} className="pl-1">{step}</li>
                                      ))}
                                    </ol>
                                  </div>
                                )}

                                {/* Home Care */}
                                {disease.homeCareTips && disease.homeCareTips.length > 0 && (
                                  <div>
                                    <h4 className="font-bold flex items-center gap-2 mb-3 border-b pb-2">
                                      <CheckCircle2 className="h-5 w-5 text-primary" /> Home Care Recommendations
                                    </h4>
                                    <ul className="space-y-2 text-sm text-foreground/90">
                                      {disease.homeCareTips.map((tip, i) => (
                                        <li key={i} className="flex items-start gap-2">
                                          <span className="text-primary font-bold mt-0.5">•</span>
                                          <span>{tip}</span>
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </div>

                              {/* Column 2 */}
                              <div className="space-y-8">
                                {/* Emergency Signs */}
                                {disease.emergencySigns && disease.emergencySigns.length > 0 && (
                                  <div className="bg-destructive/10 p-4 rounded-lg border border-destructive/20">
                                    <h4 className="font-bold text-destructive flex items-center gap-2 mb-2">
                                      <AlertCircle className="h-5 w-5" /> Warning Signs
                                    </h4>
                                    <p className="text-xs text-destructive mb-2 font-medium">
                                      Go to ER if you experience:
                                    </p>
                                    <ul className="space-y-1 text-sm text-foreground/90">
                                      {disease.emergencySigns.map((sign, i) => (
                                        <li key={i} className="flex items-start gap-2">
                                          <span className="text-destructive font-bold mt-0.5">!</span>
                                          <span>{sign}</span>
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}

                                {/* Medications to Avoid */}
                                {disease.medicationsToAvoid && disease.medicationsToAvoid.length > 0 && (
                                  <div>
                                    <h4 className="font-bold flex items-center gap-2 mb-3 border-b pb-2 text-orange-600 dark:text-orange-400">
                                      <Pill className="h-5 w-5" /> Medications to Avoid
                                    </h4>
                                    <div className="flex flex-wrap gap-2">
                                      {disease.medicationsToAvoid.map((med, i) => (
                                        <Badge key={i} variant="outline" className="border-orange-200 bg-orange-50 text-orange-800 dark:bg-orange-950/30 dark:text-orange-300">
                                          {med}
                                        </Badge>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Pregnancy-safe alternatives */}
                                {isPregnant && disease.pregnancySafeMeds && disease.pregnancySafeMeds.length > 0 && (
                                  <div className="bg-green-50 dark:bg-green-950/30 p-4 rounded-lg border border-green-200 dark:border-green-800">
                                    <h4 className="font-bold text-green-700 dark:text-green-400 flex items-center gap-2 mb-2">
                                      <Baby className="h-5 w-5" /> Pregnancy-Safe Options
                                    </h4>
                                    <p className="text-xs text-green-600 dark:text-green-500 mb-2">Safe medications during pregnancy:</p>
                                    <div className="flex flex-wrap gap-2">
                                      {disease.pregnancySafeMeds.map((med, i) => (
                                        <Badge key={i} className="bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">
                                          {med}
                                        </Badge>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Action Links */}
                            <div className="flex flex-wrap gap-3 pt-6 mt-6 border-t border-border">
                              <Link to={`/disease/${disease.id}`} className="flex-1 sm:flex-none">
                                <Button variant="outline" className="w-full">
                                  <Info className="mr-2 h-4 w-4" /> Full Disease Info
                                </Button>
                              </Link>
                              <Button 
                                className="flex-1 sm:flex-none bg-secondary hover:bg-secondary/90 text-white"
                                onClick={() => navigate('/chat-ai', { 
                                  state: { 
                                    initialMessage: `I just received a diagnosis assessment suggesting ${disease.name} as a match. ${isPregnant ? 'I am pregnant. ' : ''}Can you help explain the home care steps and tell me more about it?` 
                                  } 
                                })}
                              >
                                <MessageCircle className="mr-2 h-4 w-4" /> Discuss with AI
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

          {/* Show More/Less Button */}
          {predictions.length > 3 && (
            <motion.div variants={itemVariants} className="text-center mt-6">
              <Button
                variant="outline"
                onClick={() => setShowAllConditions(!showAllConditions)}
                className="px-8"
              >
                {showAllConditions ? 'Show Less' : `Show ${predictions.length - 3} More Conditions`}
              </Button>
            </motion.div>
          )}

          {/* Educational Note */}
          {predictions.length > 0 && predictions[0].confidence < 40 && (
            <motion.div 
              variants={itemVariants} 
              className="mt-8 p-5 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800"
            >
              <div className="flex items-start gap-3">
                <Brain className="h-6 w-6 text-blue-600 dark:text-blue-400 mt-0.5" />
                <div>
                  <h3 className="font-bold text-blue-800 dark:text-blue-300 mb-2">Low Confidence Analysis</h3>
                  <p className="text-sm text-blue-700 dark:text-blue-400">
                    The matches above have lower confidence scores. This could be because:
                  </p>
                  <ul className="list-disc list-inside mt-2 space-y-1 text-sm text-blue-700 dark:text-blue-400">
                    <li>You've selected only one symptom - many conditions share similar symptoms</li>
                    <li>Your symptoms might be caused by stress or non-medical factors</li>
                    <li>Consider providing more details about duration and severity</li>
                    <li>Try selecting additional related symptoms for better accuracy</li>
                  </ul>
                </div>
              </div>
            </motion.div>
          )}

          {/* Footer Disclaimer */}
          <motion.div variants={itemVariants} className="text-center text-sm text-muted-foreground mt-12 pb-8 p-4 bg-muted/50 rounded-lg">
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