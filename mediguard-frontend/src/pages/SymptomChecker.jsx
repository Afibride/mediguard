import React, { useState, useMemo, useEffect } from 'react';
import { Helmet } from 'react-helmet';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Loader2, Search, Thermometer, Clock, Activity, Baby, User, Info, Heart } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { getAllSymptoms, diseases as diseaseDB } from '@/data/diseases';
import { useAuth } from '@/components/AuthContext';

const SymptomChecker = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [formData, setFormData] = useState({
    duration: '',
    severity: '',
    gender: '',
    age: '',
    isPregnant: false
  });
  const [selectedSymptoms, setSelectedSymptoms] = useState([]);
  const [showPregnancyOption, setShowPregnancyOption] = useState(false);

  const allSymptoms = useMemo(() => getAllSymptoms(), []);

  // Show pregnancy option when gender is female
  useEffect(() => {
    if (formData.gender === 'female') {
      setShowPregnancyOption(true);
    } else {
      setShowPregnancyOption(false);
      setFormData(prev => ({ ...prev, isPregnant: false }));
    }
  }, [formData.gender]);

  const categoriesMap = {
    'Fever & Systemic': ['Fever', 'High fever', 'Prolonged fever', 'Sudden high fever', 'Chills', 'Sweating', 'Night sweats', 'Fatigue', 'Weakness', 'Weight loss', 'Swollen lymph nodes'],
    'Respiratory': ['Cough', 'Chronic cough', 'Shortness of breath', 'Chest pain', 'Runny nose', 'Sore throat', 'Coughing up blood', 'Wheezing'],
    'Gastrointestinal': ['Nausea', 'Vomiting', 'Diarrhea', 'Profuse watery diarrhea', 'Bloody or mucus-filled diarrhea', 'Abdominal pain', 'Constipation', 'Blood in stool'],
    'Pain & Neurological': ['Headache', 'Severe headache', 'Joint pain', 'Muscle aches', 'Muscle pain', 'Back pain', 'Stiff neck', 'Confusion', 'Dizziness', 'Sleep disturbances', 'Numbness'],
    'Skin & External': ['Rash', 'Itchy skin', 'Ring-shaped rash', 'Red, scaly, cracked skin', 'Red eyes', 'Jaundice', 'Pale skin', 'Pus or discharge', 'Skin lesions', 'Koplik spots', 'Rose spots', 'Bullseye rash'],
    'Women\'s Health': ['Missed period', 'Vaginal bleeding', 'Vaginal discharge', 'Pelvic pain', 'Breast pain', 'Nipple discharge', 'Pain during intercourse'],
    'Other Specifics': ['Visible worms in stool', 'Blood in urine', 'Unexplained bleeding', 'Vaginal itching', 'White patches in mouth', 'Increased thirst', 'Frequent urination', 'Slow-healing sores']
  };

  const handleSymptomToggle = (symptom) => {
    setSelectedSymptoms((prev) =>
      prev.includes(symptom) ? prev.filter((s) => s !== symptom) : [...prev, symptom]
    );
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  // Enhanced diagnosis algorithm with gender and pregnancy awareness
  const generatePredictionsLocal = (symptomsToAnalyze) => {
    // Filter diseases based on gender and pregnancy
    let filteredDiseases = [...diseaseDB];
    
    // Filter by gender if specified
    if (formData.gender) {
      filteredDiseases = filteredDiseases.filter(disease => {
        if (!disease.genderSpecific) return true;
        return disease.genderSpecific === formData.gender;
      });
    }
    
    // Filter by pregnancy if applicable
    if (formData.isPregnant) {
      filteredDiseases = filteredDiseases.filter(disease => {
        // Include pregnancy-specific conditions
        if (disease.pregnancyRelated) return true;
        // Exclude diseases unsafe during pregnancy
        return !disease.unsafeDuringPregnancy;
      });
    }
    
    // Age-based filtering (if age provided)
    if (formData.age) {
      const age = parseInt(formData.age);
      filteredDiseases = filteredDiseases.filter(disease => {
        if (!disease.ageRange) return true;
        const [min, max] = disease.ageRange;
        return age >= min && age <= max;
      });
    }

    return filteredDiseases
      .map((disease) => {
        let matchCount = 0;
        let confidenceBoost = 0;
        let symptomMatches = [];

        // Symptom matching with partial matches for single symptoms
        symptomsToAnalyze.forEach((symptom) => {
          const symptomLower = symptom.toLowerCase();
          
          // Check for exact matches
          if (disease.symptoms.some(s => s.toLowerCase() === symptomLower)) {
            matchCount++;
            symptomMatches.push(symptom);
          }
          
          // Check for related symptoms (partial matches for stress-related conditions)
          if (disease.relatedSymptoms?.some(s => s.toLowerCase().includes(symptomLower))) {
            confidenceBoost += 5;
          }
          
          // Check confidence factors
          if (disease.confidenceFactors?.includes(symptom)) {
            confidenceBoost += 10;
          }
        });

        // Special handling for single symptom cases (like stress)
        if (symptomsToAnalyze.length === 1 && disease.commonSingleSymptomConditions) {
          if (disease.symptoms.some(s => s.toLowerCase().includes(symptomsToAnalyze[0].toLowerCase()))) {
            confidenceBoost += 15; // Boost confidence for common single-symptom conditions
          }
        }

        // Calculate base confidence
        let confidence = 0;
        if (disease.symptoms.length > 0) {
          // Weight matches more heavily for single symptoms
          const matchWeight = symptomsToAnalyze.length === 1 ? 0.8 : 0.6;
          confidence = (matchCount / Math.min(disease.symptoms.length, 5)) * 100 * matchWeight;
        }
        
        confidence += confidenceBoost;
        
        // Adjust confidence based on severity and duration
        if (formData.severity === 'severe') {
          if (disease.severity === 'High') confidence += 15;
          else if (disease.emergencySigns?.length > 0) confidence += 10;
        }
        
        if (formData.duration === '2+ weeks' && disease.chronic) confidence += 10;
        
        // Pregnancy-specific adjustments
        if (formData.isPregnant) {
          if (disease.pregnancySafe) confidence += 5;
          if (disease.pregnancyWarning) confidence -= 10;
        }

        confidence = Math.min(Math.max(Math.round(confidence), 0), 98);

        return { 
          ...disease, 
          confidence, 
          matchCount,
          symptomMatches,
          isSingleSymptomCandidate: symptomsToAnalyze.length === 1 && matchCount > 0
        };
      })
      .filter((d) => d.matchCount > 0 || d.confidence > 20) // Include conditions with reasonable confidence
      .sort((a, b) => {
        // Sort by confidence first
        if (b.confidence !== a.confidence) return b.confidence - a.confidence;
        // Then by match count
        if (b.matchCount !== a.matchCount) return b.matchCount - a.matchCount;
        // Then by severity (high severity first)
        if (a.severity === 'High' && b.severity !== 'High') return -1;
        if (b.severity === 'High' && a.severity !== 'High') return 1;
        return 0;
      })
      .slice(0, 7); // Show top 7 matches for better options
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (selectedSymptoms.length === 0) {
      toast({
        variant: 'destructive',
        title: 'No symptoms selected',
        description: 'Please select at least one symptom to get a diagnosis.',
      });
      return;
    }

    setLoading(true);

    // Simulate processing
    setTimeout(() => {
      const results = generatePredictionsLocal(selectedSymptoms);

      // Add note for single symptom cases
      const analysisNote = selectedSymptoms.length === 1 
        ? "You've reported only one symptom. Some conditions may present with a single symptom, especially stress-related issues. Consider if you've noticed any other changes in your health."
        : null;

      navigate('/prediction-results', {
        state: {
          symptoms: selectedSymptoms,
          duration: formData.duration || 'Not specified',
          severity: formData.severity || 'Not specified',
          gender: formData.gender || 'Not specified',
          age: formData.age || 'Not specified',
          isPregnant: formData.isPregnant,
          predictions: results,
          analysisNote
        },
      });
    }, 1500);
  };

  const filteredSymptoms = allSymptoms.filter(s => 
    s.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <>
      <Helmet>
        <title>Symptom Checker - MediGuard Bamenda</title>
        <meta name="description" content="Check your symptoms with our AI-powered symptom checker. Get instant disease predictions and health recommendations." />
      </Helmet>

      <div className="min-h-screen bg-muted/30 py-12">
        <motion.div 
          className="container mx-auto px-4 max-w-5xl"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <motion.div variants={itemVariants} className="flex flex-col items-center text-center mb-8">
            <div className="mb-4">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
                <Thermometer className="h-8 w-8 text-primary" />
              </div>
            </div>
            <h1 className="text-4xl font-bold mb-4 text-foreground">Symptom Checker</h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Select the symptoms you are currently experiencing to receive a comprehensive AI-powered diagnosis assessment.
            </p>
          </motion.div>

          <form onSubmit={handleSubmit}>
            
            {/* Personal Information Card */}
            <motion.div variants={itemVariants}>
              <Card className="mb-6 shadow-md border-t-4 border-t-primary">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="h-5 w-5 text-primary" />
                    Personal Information (Optional but Recommended)
                  </CardTitle>
                  <CardDescription>
                    Providing these details helps us give you more accurate results
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Gender Selection */}
                    <div className="space-y-3">
                      <Label className="text-foreground font-medium flex items-center gap-2">
                        <User className="h-4 w-4 text-muted-foreground" /> Gender
                      </Label>
                      <RadioGroup
                        name="gender"
                        value={formData.gender}
                        onValueChange={(value) => setFormData(prev => ({ ...prev, gender: value }))}
                        className="flex space-x-4"
                      >
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="male" id="male" />
                          <Label htmlFor="male">Male</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="female" id="female" />
                          <Label htmlFor="female">Female</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem value="other" id="other" />
                          <Label htmlFor="other">Other</Label>
                        </div>
                      </RadioGroup>
                    </div>

                    {/* Age Input */}
                    <div className="space-y-2">
                      <Label htmlFor="age" className="text-foreground font-medium flex items-center gap-2">
                        <Clock className="h-4 w-4 text-muted-foreground" /> Age
                      </Label>
                      <Input
                        id="age"
                        name="age"
                        type="number"
                        min="0"
                        max="120"
                        value={formData.age}
                        onChange={handleInputChange}
                        placeholder="Enter your age"
                        className="h-11"
                      />
                    </div>

                    {/* Pregnancy Option (conditional) */}
                    {showPregnancyOption && (
                      <div className="md:col-span-2 flex items-center space-x-2 p-4 bg-primary/5 rounded-lg border border-primary/20">
                        <Checkbox
                          id="isPregnant"
                          name="isPregnant"
                          checked={formData.isPregnant}
                          onCheckedChange={(checked) => 
                            setFormData(prev => ({ ...prev, isPregnant: checked }))
                          }
                        />
                        <Label htmlFor="isPregnant" className="flex items-center gap-2 cursor-pointer">
                          <Baby className="h-4 w-4 text-primary" />
                          <span className="font-medium">I am currently pregnant</span>
                          <span className="text-sm text-muted-foreground">
                            (This helps us provide pregnancy-safe recommendations)
                          </span>
                        </Label>
                      </div>
                    )}

                    {/* Duration and Severity */}
                    <div className="space-y-2">
                      <Label htmlFor="duration" className="text-foreground font-medium flex items-center gap-2">
                        <Clock className="h-4 w-4 text-muted-foreground" /> Symptom Duration
                      </Label>
                      <select
                        id="duration"
                        name="duration"
                        value={formData.duration}
                        onChange={handleInputChange}
                        className="flex h-11 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring shadow-sm"
                      >
                        <option value="">Select duration...</option>
                        <option value="1-3 days">1 to 3 days</option>
                        <option value="3-7 days">3 to 7 days</option>
                        <option value="1-2 weeks">1 to 2 weeks</option>
                        <option value="2+ weeks">More than 2 weeks</option>
                      </select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="severity" className="text-foreground font-medium flex items-center gap-2">
                        <Activity className="h-4 w-4 text-muted-foreground" /> Overall Severity
                      </Label>
                      <select
                        id="severity"
                        name="severity"
                        value={formData.severity}
                        onChange={handleInputChange}
                        className="flex h-11 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring shadow-sm"
                      >
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

            {/* Search Bar */}
            <motion.div variants={itemVariants} className="mb-6 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search specific symptoms (e.g., headache, fever)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-12 h-12 text-base bg-background shadow-sm border-input"
              />
            </motion.div>

            {/* Selected Symptoms Counter */}
            {selectedSymptoms.length > 0 && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="mb-4 p-3 bg-primary/10 rounded-lg flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <Info className="h-5 w-5 text-primary" />
                  <span className="font-medium">
                    {selectedSymptoms.length} symptom{selectedSymptoms.length !== 1 ? 's' : ''} selected
                  </span>
                </div>
                {selectedSymptoms.length === 1 && (
                  <span className="text-sm text-muted-foreground">
                    Single symptom analysis enabled
                  </span>
                )}
              </motion.div>
            )}

            {/* Symptom List */}
            {searchQuery.length > 0 ? (
              <motion.div variants={itemVariants}>
                <Card className="mb-6 border-2 border-primary/20 shadow-md">
                  <CardHeader className="pb-3 border-b">
                    <CardTitle>Search Results</CardTitle>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {filteredSymptoms.map((symptom) => (
                        <div key={symptom} className="flex items-center space-x-3 bg-muted/40 p-3 rounded-lg hover:bg-muted/70 transition-colors border border-transparent hover:border-border">
                          <Checkbox
                            id={symptom}
                            checked={selectedSymptoms.includes(symptom)}
                            onCheckedChange={() => handleSymptomToggle(symptom)}
                            className="h-5 w-5"
                          />
                          <Label htmlFor={symptom} className="text-sm font-medium cursor-pointer text-foreground flex-1 leading-tight">
                            {symptom}
                          </Label>
                        </div>
                      ))}
                    </div>
                    {filteredSymptoms.length === 0 && (
                      <p className="text-muted-foreground mt-4 text-center py-4">
                        No symptoms found matching your search.
                      </p>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            ) : (
              Object.entries(categoriesMap).map(([category, symptoms], idx) => (
                <motion.div key={category} variants={itemVariants}>
                  <Card className="mb-6 shadow-sm hover:shadow-md transition-all border-border overflow-hidden">
                    <CardHeader className="bg-muted/30 border-b pb-3 py-4">
                      <CardTitle className="text-lg font-semibold text-foreground flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-primary"></div>
                        {category}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="pt-4">
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-y-3 gap-x-6">
                        {symptoms.map((symptom) => {
                          if (!allSymptoms.includes(symptom)) return null;
                          return (
                            <div key={symptom} className="flex items-start space-x-3 p-2 rounded-md hover:bg-muted/40 transition-colors">
                              <Checkbox
                                id={symptom}
                                checked={selectedSymptoms.includes(symptom)}
                                onCheckedChange={() => handleSymptomToggle(symptom)}
                                className="mt-0.5"
                              />
                              <Label
                                htmlFor={symptom}
                                className="text-sm font-medium cursor-pointer text-foreground flex-1 leading-tight"
                              >
                                {symptom}
                              </Label>
                            </div>
                          );
                        })}
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))
            )}

            {/* Sticky Bottom Bar for Selected Symptoms */}
            {selectedSymptoms.length > 0 && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }} 
                animate={{ opacity: 1, y: 0 }} 
                className="sticky bottom-4 z-20 mx-auto w-full"
              >
                <Card className="mb-4 border-primary/50 bg-background/95 backdrop-blur shadow-2xl">
                  <div className="p-3 px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="flex-1 overflow-x-auto hide-scrollbar whitespace-nowrap py-1 flex items-center gap-2">
                      <span className="text-sm font-semibold text-foreground mr-2 shrink-0">
                        Selected ({selectedSymptoms.length}):
                      </span>
                      {selectedSymptoms.map((symptom) => (
                        <span
                          key={symptom}
                          className="inline-flex items-center px-3 py-1 bg-primary text-primary-foreground rounded-full text-xs font-medium cursor-pointer hover:bg-destructive hover:text-destructive-foreground transition-colors shrink-0"
                          onClick={() => handleSymptomToggle(symptom)}
                        >
                          {symptom} <span className="ml-1 opacity-70">✕</span>
                        </span>
                      ))}
                    </div>
                  </div>
                </Card>
              </motion.div>
            )}

            {/* Action Buttons */}
            <motion.div variants={itemVariants} className="flex flex-col sm:flex-row justify-center mt-8 pb-16 gap-4">
              <Button
                type="submit"
                size="lg"
                disabled={loading}
                className="w-full sm:w-auto px-12 h-14 text-lg font-bold shadow-xl hover:shadow-2xl transition-all bg-primary text-primary-foreground"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-6 w-6 animate-spin" />
                    Analyzing Symptoms...
                  </>
                ) : (
                  'Get Diagnosis'
                )}
              </Button>
            </motion.div>
          </form>
        </motion.div>
      </div>
    </>
  );
};

export default SymptomChecker;