
import React, { useState } from 'react';
import { Helmet } from 'react-helmet';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { KeyRound, ArrowRight } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

const ResetPasswordPage = () => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      toast({
        variant: "destructive",
        title: "Passwords don't match",
        description: "Please make sure your passwords match.",
      });
      return;
    }
    
    if (password.length < 6) {
      toast({
        variant: "destructive",
        title: "Password too short",
        description: "Password must be at least 6 characters.",
      });
      return;
    }

    setLoading(true);
    
    setTimeout(() => {
      setLoading(false);
      setSuccess(true);
      toast({
        title: "Password Updated",
        description: "Your password has been successfully reset.",
      });
    }, 1500);
  };

  return (
    <>
      <Helmet>
        <title>Create New Password - MediGuard Bamenda</title>
        <meta name="description" content="Set a new password for your MediGuard account." />
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
              <CardTitle className="text-2xl font-bold">Create New Password</CardTitle>
              <CardDescription>
                Enter your new password below
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {success ? (
                <div className="text-center space-y-6 py-4">
                  <div className="bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 p-4 rounded-lg">
                    <KeyRound className="h-8 w-8 mx-auto mb-2" />
                    <p className="font-medium">Password successfully updated!</p>
                  </div>
                  <Button className="w-full" onClick={() => navigate('/login')}>
                    Proceed to Login <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="password">New Password</Label>
                    <Input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      className="bg-white text-gray-900 dark:bg-slate-900 dark:text-gray-100 focus:ring-primary"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="confirmPassword">Confirm New Password</Label>
                    <Input
                      id="confirmPassword"
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                      className="bg-white text-gray-900 dark:bg-slate-900 dark:text-gray-100 focus:ring-primary"
                    />
                  </div>
                  <Button type="submit" className="w-full h-11 text-base transition-transform active:scale-[0.98] mt-2" disabled={loading || !password || !confirmPassword}>
                    {loading ? 'Updating Password...' : 'Update Password'}
                  </Button>
                </form>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </>
  );
};

export default ResetPasswordPage;
