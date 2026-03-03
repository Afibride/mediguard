
import React, { useState } from 'react';
import { Helmet } from 'react-helmet';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Mail, ArrowLeft } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

const ForgotPasswordPage = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) return;

    setLoading(true);

    setTimeout(() => {
      setLoading(false);
      setSubmitted(true);
      toast({
        title: "Reset Link Sent",
        description: "If an account exists with this email, a reset link has been sent.",
      });
    }, 1500);
  };

  return (
    <>
      <Helmet>
        <title>Forgot Password - MediGuard Bamenda</title>
        <meta name="description" content="Reset your MediGuard Bamenda account password." />
      </Helmet>

      <div className="min-h-[80vh] flex items-center justify-center bg-muted/30 px-4 py-12">
        <motion.div
          className="w-full max-w-md"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Card className="shadow-xl border-t-4 border-t-primary">
            <CardHeader className="space-y-1 text-center bg-white dark:bg-slate-950 rounded-t-xl">
              <div className="flex justify-center mb-4">
                <img 
                  src="/public/mediguard.png" 
                  alt="MediGuard Logo" 
                  className="logo-md"
                />
              </div>
              <CardTitle className="text-2xl font-bold">Reset Password</CardTitle>
              <CardDescription>
                Enter your email to receive a password reset link
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {submitted ? (
                <div className="text-center space-y-4 py-4">
                  <div className="bg-primary/10 text-primary p-4 rounded-lg">
                    <Mail className="h-8 w-8 mx-auto mb-2" />
                    <p className="text-sm font-medium">Check your email for the reset link.</p>
                  </div>
                  <Button variant="outline" className="w-full" onClick={() => setSubmitted(false)}>
                    Try another email
                  </Button>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email Address</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="m.doe@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      className="bg-white text-gray-900 dark:bg-slate-900 dark:text-gray-100 focus:ring-primary"
                    />
                  </div>
                  <Button type="submit" className="w-full h-11 text-base transition-transform active:scale-[0.98]" disabled={loading || !email}>
                    {loading ? 'Sending Link...' : 'Send Reset Link'}
                  </Button>
                </form>
              )}
            </CardContent>
            <CardFooter className="flex flex-col space-y-4 pb-8">
              <div className="text-center text-sm text-muted-foreground w-full">
                <Link to="/login" className="flex items-center justify-center text-primary font-medium hover:underline">
                  <ArrowLeft className="mr-2 h-4 w-4" /> Back to Login
                </Link>
              </div>
            </CardFooter>
          </Card>
        </motion.div>
      </div>
    </>
  );
};

export default ForgotPasswordPage;
