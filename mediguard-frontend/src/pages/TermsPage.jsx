
import React from 'react';
import { Helmet } from 'react-helmet';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Shield } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

const TermsPage = () => {
  const navigate = useNavigate();

  return (
    <>
      <Helmet>
        <title>Terms of Service - MediGuard Bamenda</title>
        <meta name="description" content="Terms of Service and legal agreements for using MediGuard Bamenda." />
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
                Print Terms
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
                  <Shield className="h-8 w-8 text-primary" />
                  <h1 className="text-4xl font-bold m-0">Terms of Service</h1>
                </div>
                
                <p className="text-muted-foreground mb-8">Last Updated: October 2023</p>

                <div className="space-y-8">
                  <section>
                    <h2 className="text-2xl font-semibold text-foreground">1. Acceptance of Terms</h2>
                    <p>By accessing and using MediGuard Bamenda ("the Service"), you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by these terms, please do not use this Service.</p>
                  </section>

                  <section>
                    <h2 className="text-2xl font-semibold text-foreground">2. Medical Disclaimer - Not Professional Advice</h2>
                    <div className="bg-destructive/10 p-4 rounded-md border-l-4 border-destructive text-destructive-foreground">
                      <p className="font-bold m-0">CRITICAL: MediGuard Bamenda is an AI-powered informational tool, NOT a substitute for professional medical advice, diagnosis, or treatment.</p>
                    </div>
                    <p className="mt-4">The predictions, Chat AI responses, and first aid tips provided by the Service are for educational purposes based on general data. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition. Never disregard professional medical advice or delay in seeking it because of something you have read on this Service.</p>
                    <p><strong>If you think you may have a medical emergency, call your doctor, go to the nearest hospital, or call emergency services immediately.</strong></p>
                  </section>

                  <section>
                    <h2 className="text-2xl font-semibold text-foreground">3. User Responsibilities</h2>
                    <p>You agree to:</p>
                    <ul>
                      <li>Provide accurate and complete information about your health and symptoms to the best of your knowledge.</li>
                      <li>Use the Service for lawful purposes only.</li>
                      <li>Not use the Service in emergencies where immediate physical medical attention is required.</li>
                      <li>Keep your account credentials secure and confidential.</li>
                    </ul>
                  </section>

                  <section>
                    <h2 className="text-2xl font-semibold text-foreground">4. Limitation of Liability</h2>
                    <p>Under no circumstances shall MediGuard Bamenda, its developers, or affiliates be liable for any direct, indirect, incidental, special, or consequential damages that result from the use of, or the inability to use, the Service. This includes reliance on any information obtained from the Service, or that result from mistakes, omissions, interruptions, deletion of files, viruses, errors, defects, or any failure of performance.</p>
                  </section>

                  <section>
                    <h2 className="text-2xl font-semibold text-foreground">5. Privacy and Data Security</h2>
                    <p>Your use of the Service is also governed by our Privacy Policy. By using the Service, you consent to the collection, use, and sharing of your information as described in the Privacy Policy.</p>
                  </section>

                  <section>
                    <h2 className="text-2xl font-semibold text-foreground">6. Intellectual Property</h2>
                    <p>All content, features, and functionality of the Service, including but not limited to AI models, text, graphics, logos, and software, are the exclusive property of MediGuard Bamenda and are protected by international copyright, trademark, patent, trade secret, and other intellectual property laws.</p>
                  </section>

                  <section>
                    <h2 className="text-2xl font-semibold text-foreground">7. Modifications to Terms</h2>
                    <p>We reserve the right to modify these terms at any time. We will notify users of any significant changes. Your continued use of the Service following such modifications constitutes your acceptance of the revised terms.</p>
                  </section>

                  <section>
                    <h2 className="text-2xl font-semibold text-foreground">8. Termination</h2>
                    <p>We may terminate or suspend access to our Service immediately, without prior notice or liability, for any reason whatsoever, including without limitation if you breach the Terms.</p>
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

export default TermsPage;
