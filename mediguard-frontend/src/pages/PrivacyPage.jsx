
import React from 'react';
import { Helmet } from 'react-helmet';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Lock } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

const PrivacyPage = () => {
  const navigate = useNavigate();

  return (
    <>
      <Helmet>
        <title>Privacy Policy - MediGuard Bamenda</title>
        <meta name="description" content="Privacy Policy detailing how MediGuard Bamenda handles your health data." />
      </Helmet>

      <div className="min-h-screen bg-muted/30 py-12">
        <div className="container mx-auto px-4 max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="mb-6 flex justify-between items-center print:hidden">
              <Button variant="ghost" onClick={() => navigate(-1)} className="hover:bg-primary/10">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Button>

              <div className="hidden sm:block">
                <img 
                  src="/public/mediguard.png" 
                  alt="MediGuard Logo" 
                  className="logo-sm"
                />
              </div>

              <Button variant="outline" onClick={() => window.print()}>
                Print Policy
              </Button>
            </div>

            <Card className="shadow-lg border-t-4 border-t-primary">
              <CardContent className="p-8 md:p-12 prose prose-slate dark:prose-invert max-w-none">
                <div className="sm:hidden mb-6 flex justify-center">
                  <img 
                    src="/public/mediguard.png" 
                    alt="MediGuard Logo" 
                    className="logo-sm"
                  />
                </div>

                <div className="flex items-center gap-3 mb-8 border-b pb-6">
                  <Lock className="h-8 w-8 text-primary" />
                  <h1 className="text-4xl font-bold m-0">Privacy Policy</h1>
                </div>
                
                <p className="text-muted-foreground mb-8">Last Updated: October 2023</p>

                <div className="space-y-8">
                  <section>
                    <h2 className="text-2xl font-semibold text-foreground">1. Introduction</h2>
                    <p>MediGuard Bamenda is committed to protecting your privacy, especially regarding your sensitive health information. This policy explains how we collect, use, and safeguard your data when you use our symptom checker, AI chat, and related services.</p>
                  </section>

                  <section>
                    <h2 className="text-2xl font-semibold text-foreground">2. Information We Collect</h2>
                    <p>We collect the following types of information:</p>
                    <ul>
                      <li><strong>Account Information:</strong> Email address or phone number, password, age, gender, and blood type.</li>
                      <li><strong>Health Data:</strong> Symptoms you report, chronic conditions, inherited illnesses, allergies, current medications, and chat histories with our AI.</li>
                      <li><strong>Usage Data:</strong> How you interact with our application, which helps us improve our services.</li>
                    </ul>
                  </section>

                  <section>
                    <h2 className="text-2xl font-semibold text-foreground">3. How We Use Your Data</h2>
                    <p>Your data is utilized strictly for the following purposes:</p>
                    <ul>
                      <li>To provide personalized health predictions and AI chat responses.</li>
                      <li>To maintain your personal health history for your reference.</li>
                      <li>To improve our AI models and the accuracy of local disease tracking (anonymized data only).</li>
                      <li>To communicate with you regarding your account or critical system updates.</li>
                    </ul>
                  </section>

                  <section>
                    <h2 className="text-2xl font-semibold text-foreground">4. Data Security</h2>
                    <p>We implement industry-standard security measures to protect your personal information. All health data is encrypted in transit and at rest. We utilize secure database solutions (like Supabase) that comply with modern data protection standards. However, no electronic transmission over the internet is entirely secure, and we cannot guarantee absolute security.</p>
                  </section>

                  <section>
                    <h2 className="text-2xl font-semibold text-foreground">5. Sharing Your Information</h2>
                    <p><strong>We do not sell your personal health data to third parties.</strong> We may share anonymized, aggregated data with local health authorities in Bamenda to assist with public health monitoring (e.g., tracking a malaria outbreak). You will never be personally identifiable in these reports.</p>
                  </section>

                  <section>
                    <h2 className="text-2xl font-semibold text-foreground">6. Your Rights</h2>
                    <p>You have the right to:</p>
                    <ul>
                      <li>Access the personal data we hold about you.</li>
                      <li>Request correction of inaccurate data.</li>
                      <li>Delete your account and all associated health history at any time.</li>
                      <li>Opt-out of optional data collection features.</li>
                    </ul>
                  </section>

                  <section>
                    <h2 className="text-2xl font-semibold text-foreground">7. Cookies and Tracking</h2>
                    <p>We use essential cookies to maintain your session and security. We may use analytics cookies to understand how our site is used, but these do not track your specific health inputs across the web.</p>
                  </section>

                  <section>
                    <h2 className="text-2xl font-semibold text-foreground">8. Contact Us</h2>
                    <p>If you have any questions or concerns about this Privacy Policy or our data practices, please contact us at:</p>
                    <p>Email: privacy@mediguard.cm<br />Address: Bamenda, Northwest Region</p>
                  </section>
                </div>

              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </>
  );
};

export default PrivacyPage;
