
import React, { useState } from 'react';
import { Helmet } from 'react-helmet';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { useAuth } from '@/components/AuthContext';
import { UserPlus, Activity, ShieldCheck, CheckCircle2, XCircle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

const SignupPage = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    gender: '',
    age: '',
    bloodType: '',
    chronicConditions: [],
    inheritedIllnesses: '',
    allergies: '',
    medications: '',
    termsAccepted: false,
    privacyAccepted: false
  });
  const [usernameValid, setUsernameValid] = useState(null);
  const [loading, setLoading] = useState(false);
  const { signup } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const chronicOptions = ['Diabetes', 'Hypertension', 'Asthma', 'Heart Disease', 'Kidney Disease', 'Liver Disease', 'Cancer', 'HIV/AIDS', 'Tuberculosis', 'Other'];

  const validateUsername = (val) => {
    if (!val) return null;
    const isValid = /^[a-zA-Z0-9_]{3,20}$/.test(val);
    return isValid;
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    if (type === 'checkbox' && name !== 'termsAccepted' && name !== 'privacyAccepted') {
      return;
    }
    
    if (name === 'username') {
      setUsernameValid(validateUsername(value));
    }

    setFormData(prev => ({ 
      ...prev, 
      [name]: type === 'checkbox' ? checked : value 
    }));
  };

  const handleChronicChange = (condition, isChecked) => {
    setFormData(prev => {
      const updatedConditions = isChecked 
        ? [...prev.chronicConditions, condition]
        : prev.chronicConditions.filter(c => c !== condition);
      return { ...prev, chronicConditions: updatedConditions };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (usernameValid === false) {
      toast({ variant: "destructive", title: "Invalid Username", description: "Username must be 3-20 characters long, containing only letters, numbers, and underscores." });
      return;
    }

    if (!formData.email && !formData.phone) {
      toast({ variant: "destructive", title: "Missing Information", description: "Please provide either an email or a phone number." });
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      toast({ variant: "destructive", title: "Passwords do not match", description: "Please ensure your passwords match." });
      return;
    }

    if (formData.password.length < 6) {
      toast({ variant: "destructive", title: "Weak Password", description: "Password must be at least 6 characters long." });
      return;
    }

    if (!formData.termsAccepted || !formData.privacyAccepted) {
      toast({ variant: "destructive", title: "Action Required", description: "You must accept the Terms and Privacy Policy." });
      return;
    }

    setLoading(true);

    const userData = {
      username: formData.username,
      email: formData.email,
      phone: formData.phone,
      password: formData.password,
      gender: formData.gender,
      age: parseInt(formData.age, 10),
      profile: {
        bloodType: formData.bloodType,
        chronicConditions: formData.chronicConditions,
        inheritedIllnesses: formData.inheritedIllnesses,
        allergies: formData.allergies,
        medications: formData.medications
      }
    };

    const success = await signup(userData);
    if (success) {
      navigate('/');
    }
    setLoading(false);
  };

  return (
    <>
      <Helmet>
        <title>Sign Up - MediGuard Bamenda</title>
        <meta name="description" content="Create a comprehensive health profile on MediGuard." />
      </Helmet>

      <div className="min-h-screen bg-muted/30 py-12 px-4">
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="container mx-auto max-w-3xl"
        >
          <Card className="shadow-2xl border-t-4 border-t-primary">
            <CardHeader className="space-y-1 text-center bg-white dark:bg-slate-950 rounded-t-xl">
              <div className="flex justify-center mb-4">
                <img 
                  src="/public/mediguard.png" 
                  alt="MediGuard Logo" 
                  className="logo-md"
                />
              </div>
              <CardTitle className="text-3xl font-bold">Create Health Profile</CardTitle>
              <CardDescription className="text-base">
                Join MediGuard Bamenda for personalized, AI-driven health insights
              </CardDescription>
            </CardHeader>
            
            <form onSubmit={handleSubmit}>
              <CardContent className="space-y-8 pt-8">
                
                {/* Account Details */}
                <motion.div 
                  initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}
                  className="space-y-4"
                >
                  <div className="flex items-center gap-2 border-b pb-2">
                    <UserPlus className="text-primary h-5 w-5" />
                    <h3 className="text-lg font-semibold text-foreground">Account Details</h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2 md:col-span-2">
                      <Label htmlFor="username">Username <span className="text-red-500">*</span></Label>
                      <div className="relative">
                        <Input 
                          id="username" 
                          name="username" 
                          placeholder="Choose a unique username" 
                          value={formData.username} 
                          onChange={handleChange} 
                          required
                          className={`bg-white text-gray-900 dark:bg-slate-900 dark:text-gray-100 pr-10 ${usernameValid === false ? 'border-destructive focus-visible:ring-destructive' : ''}`} 
                        />
                        <div className="absolute right-3 top-1/2 -translate-y-1/2">
                          {usernameValid === true && <CheckCircle2 className="h-5 w-5 text-green-500" />}
                          {usernameValid === false && <XCircle className="h-5 w-5 text-destructive" />}
                        </div>
                      </div>
                      {usernameValid === false && (
                        <p className="text-xs text-destructive">3-20 chars, alphanumeric and underscores only.</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Email Address</Label>
                      <Input id="email" name="email" type="email" placeholder="m.doe@example.com" value={formData.email} onChange={handleChange} className="bg-white text-gray-900 dark:bg-slate-900 dark:text-gray-100" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="phone">Phone Number</Label>
                      <Input id="phone" name="phone" type="tel" placeholder="+237..." value={formData.phone} onChange={handleChange} className="bg-white text-gray-900 dark:bg-slate-900 dark:text-gray-100" />
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="password">Password <span className="text-red-500">*</span></Label>
                      <Input id="password" name="password" type="password" required value={formData.password} onChange={handleChange} className="bg-white text-gray-900 dark:bg-slate-900 dark:text-gray-100" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="confirmPassword">Confirm Password <span className="text-red-500">*</span></Label>
                      <Input id="confirmPassword" name="confirmPassword" type="password" required value={formData.confirmPassword} onChange={handleChange} className="bg-white text-gray-900 dark:bg-slate-900 dark:text-gray-100" />
                    </div>
                  </div>
                </motion.div>

                {/* Basic Demographics */}
                <motion.div 
                  initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}
                  className="space-y-4"
                >
                  <div className="flex items-center gap-2 border-b pb-2">
                    <Activity className="text-primary h-5 w-5" />
                    <h3 className="text-lg font-semibold text-foreground">Basic Demographics</h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="gender">Gender <span className="text-red-500">*</span></Label>
                      <select id="gender" name="gender" value={formData.gender} onChange={handleChange} required className="flex h-10 w-full rounded-md border border-input bg-white px-3 py-2 text-sm text-gray-900 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring dark:bg-slate-900 dark:text-gray-100">
                        <option value="" disabled>Select Gender</option>
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="age">Age <span className="text-red-500">*</span></Label>
                      <Input id="age" name="age" type="number" min="1" max="120" placeholder="E.g. 30" required value={formData.age} onChange={handleChange} className="bg-white text-gray-900 dark:bg-slate-900 dark:text-gray-100" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="bloodType">Blood Type</Label>
                      <select id="bloodType" name="bloodType" value={formData.bloodType} onChange={handleChange} className="flex h-10 w-full rounded-md border border-input bg-white px-3 py-2 text-sm text-gray-900 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring dark:bg-slate-900 dark:text-gray-100">
                        <option value="">Unknown</option>
                        {['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-'].map(type => (
                          <option key={type} value={type}>{type}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </motion.div>

                {/* Medical History */}
                <motion.div 
                  initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}
                  className="space-y-4"
                >
                  <div className="flex items-center gap-2 border-b pb-2">
                    <ShieldCheck className="text-primary h-5 w-5" />
                    <h3 className="text-lg font-semibold text-foreground">Medical History (Optional)</h3>
                  </div>
                  
                  <div className="space-y-3">
                    <Label className="text-base">Chronic Conditions</Label>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 bg-muted/20 p-4 rounded-lg border">
                      {chronicOptions.map(condition => (
                        <div key={condition} className="flex items-center space-x-2">
                          <Checkbox 
                            id={`cond-${condition}`} 
                            checked={formData.chronicConditions.includes(condition)}
                            onCheckedChange={(checked) => handleChronicChange(condition, checked)}
                          />
                          <Label htmlFor={`cond-${condition}`} className="text-sm font-normal cursor-pointer">{condition}</Label>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                    <div className="space-y-2">
                      <Label htmlFor="inheritedIllnesses">Inherited Illnesses (Family History)</Label>
                      <Input id="inheritedIllnesses" name="inheritedIllnesses" placeholder="E.g. Sickle Cell, Diabetes" value={formData.inheritedIllnesses} onChange={handleChange} className="bg-white text-gray-900 dark:bg-slate-900 dark:text-gray-100" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="allergies">Known Allergies</Label>
                      <Input id="allergies" name="allergies" placeholder="E.g. Penicillin, Peanuts" value={formData.allergies} onChange={handleChange} className="bg-white text-gray-900 dark:bg-slate-900 dark:text-gray-100" />
                    </div>
                    <div className="space-y-2 md:col-span-2">
                      <Label htmlFor="medications">Current Medications</Label>
                      <Input id="medications" name="medications" placeholder="List any medications you take regularly" value={formData.medications} onChange={handleChange} className="bg-white text-gray-900 dark:bg-slate-900 dark:text-gray-100" />
                    </div>
                  </div>
                </motion.div>

                {/* Terms and Privacy */}
                <motion.div 
                  initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
                  className="space-y-3 pt-4 border-t"
                >
                  <div className="flex items-center space-x-2">
                    <Checkbox id="termsAccepted" name="termsAccepted" checked={formData.termsAccepted} onCheckedChange={(c) => setFormData(p => ({...p, termsAccepted: c}))} required />
                    <Label htmlFor="termsAccepted" className="text-sm font-normal cursor-pointer text-muted-foreground">
                      I have read and agree to the <Link to="/terms" className="text-primary hover:underline font-medium">Terms of Service</Link> <span className="text-red-500">*</span>
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox id="privacyAccepted" name="privacyAccepted" checked={formData.privacyAccepted} onCheckedChange={(c) => setFormData(p => ({...p, privacyAccepted: c}))} required />
                    <Label htmlFor="privacyAccepted" className="text-sm font-normal cursor-pointer text-muted-foreground">
                      I acknowledge and accept the <Link to="/privacy" className="text-primary hover:underline font-medium">Privacy Policy</Link> regarding my health data <span className="text-red-500">*</span>
                    </Label>
                  </div>
                </motion.div>

              </CardContent>
              <CardFooter className="flex flex-col space-y-4 pb-8">
                <Button type="submit" className="w-full text-lg h-12" disabled={loading}>
                  {loading ? 'Creating Secure Profile...' : 'Complete Registration'}
                </Button>
                <div className="text-center text-sm text-muted-foreground">
                  Already have an account?{' '}
                  <Link to="/login" className="text-primary font-medium hover:underline">
                    Login securely
                  </Link>
                </div>
              </CardFooter>
            </form>
          </Card>
        </motion.div>
      </div>
    </>
  );
};

export default SignupPage;
