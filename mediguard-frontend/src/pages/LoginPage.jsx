
import React, { useState } from 'react';
import { Helmet } from 'react-helmet';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { useAuth } from '@/components/AuthContext';
import { LogIn } from 'lucide-react';

const LoginPage = () => {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const isEmail = identifier.includes('@');
    const credentials = {
      [isEmail ? 'email' : 'phone']: identifier,
      password
    };

    const success = await login(credentials);
    if (success) {
      navigate(from, { replace: true });
    }
    setLoading(false);
  };

  const containerVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5, staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <>
      <Helmet>
        <title>Login - MediGuard Bamenda</title>
        <meta name="description" content="Login to your MediGuard account to access personalized health screening tools." />
      </Helmet>

      <div className="min-h-[80vh] flex items-center justify-center bg-muted/30 px-4 py-12">
        <motion.div
          className="w-full max-w-md"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <Card className="shadow-xl border-t-4 border-t-primary">
            <CardHeader className="space-y-1 text-center bg-white dark:bg-slate-950 rounded-t-xl">
              <motion.div variants={itemVariants} className="flex justify-center mb-4">
                <img 
                  src="/public/mediguard.png" 
                  alt="MediGuard Logo" 
                  className="logo-md"
                />
              </motion.div>
              <motion.div variants={itemVariants}>
                <CardTitle className="text-2xl font-bold">Welcome Back</CardTitle>
                <CardDescription>
                  Enter your email or phone number to sign in
                </CardDescription>
              </motion.div>
            </CardHeader>
            <form onSubmit={handleSubmit}>
              <CardContent className="space-y-4 pt-6">
                <motion.div variants={itemVariants} className="space-y-2">
                  <Label htmlFor="identifier">Email or Phone Number</Label>
                  <Input
                    id="identifier"
                    type="text"
                    placeholder="m.doe@example.com or +237..."
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    required
                    className="bg-white text-gray-900 dark:bg-slate-900 dark:text-gray-100 focus:ring-primary"
                  />
                </motion.div>
                <motion.div variants={itemVariants} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="password">Password</Label>
                    <Link to="/forgot-password" className="text-xs text-primary hover:underline">
                      Forgot password?
                    </Link>
                  </div>
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="bg-white text-gray-900 dark:bg-slate-900 dark:text-gray-100 focus:ring-primary"
                  />
                </motion.div>
                <motion.div variants={itemVariants} className="flex items-center space-x-2 pt-2">
                  <Checkbox id="remember" />
                  <Label htmlFor="remember" className="text-sm font-normal cursor-pointer text-muted-foreground">
                    Remember me for 30 days
                  </Label>
                </motion.div>
              </CardContent>
              <CardFooter className="flex flex-col space-y-4 pb-8">
                <motion.div variants={itemVariants} className="w-full">
                  <Button type="submit" className="w-full h-11 text-base transition-transform active:scale-[0.98]" disabled={loading || !identifier || !password}>
                    {loading ? 'Signing in...' : (
                      <>
                        <LogIn className="mr-2 h-4 w-4" /> Sign In
                      </>
                    )}
                  </Button>
                </motion.div>
                <motion.div variants={itemVariants} className="text-center text-sm text-muted-foreground">
                  Don't have an account?{' '}
                  <Link to="/signup" className="text-primary font-medium hover:underline">
                    Sign up
                  </Link>
                </motion.div>
              </CardFooter>
            </form>
          </Card>
        </motion.div>
      </div>
    </>
  );
};

export default LoginPage;
