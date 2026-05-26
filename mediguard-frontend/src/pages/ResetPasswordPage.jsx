import React, { useEffect, useRef, useState } from 'react';
import { Helmet } from 'react-helmet';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { KeyRound, ArrowRight, Mail, RefreshCw } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { forgotPassword, resetPassword } from '@/services/api';

// ─── 6-digit OTP input ────────────────────────────────────────────────────────
const OtpInput = ({ value, onChange }) => {
  const digits = (value + '      ').slice(0, 6).split('');
  const refs = useRef([]);

  const handleKey = (i, e) => {
    if (e.key === 'Backspace') {
      const next = value.slice(0, i) + value.slice(i + 1);
      onChange(next);
      if (i > 0) refs.current[i - 1]?.focus();
      return;
    }
    if (e.key === 'ArrowLeft' && i > 0) { refs.current[i - 1]?.focus(); return; }
    if (e.key === 'ArrowRight' && i < 5) { refs.current[i + 1]?.focus(); return; }
  };

  const handleChange = (i, e) => {
    const ch = e.target.value.replace(/\D/g, '').slice(-1);
    if (!ch) return;
    const arr = digits.map(d => d.trim());
    arr[i] = ch;
    const next = arr.join('').replace(/\s/g, '').slice(0, 6);
    onChange(next);
    if (i < 5) refs.current[i + 1]?.focus();
  };

  const handlePaste = (e) => {
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (pasted) { onChange(pasted); refs.current[Math.min(pasted.length, 5)]?.focus(); }
    e.preventDefault();
  };

  return (
    <div className="flex gap-2 justify-center" onPaste={handlePaste}>
      {digits.map((d, i) => (
        <input
          key={i}
          ref={el => refs.current[i] = el}
          type="text"
          inputMode="numeric"
          maxLength={1}
          value={d.trim()}
          onChange={e => handleChange(i, e)}
          onKeyDown={e => handleKey(i, e)}
          className={`w-11 h-14 text-center text-xl font-bold rounded-lg border-2 bg-white dark:bg-slate-900
            focus:outline-none focus:ring-2 focus:ring-primary transition-colors
            ${d.trim() ? 'border-primary text-foreground' : 'border-muted-foreground/30 text-muted-foreground'}`}
        />
      ))}
    </div>
  );
};

// ─── Main page ────────────────────────────────────────────────────────────────
const ResetPasswordPage = () => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [success, setSuccess] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // URL may carry ?token=<long-token>  (clicked email link)
  //              or ?email=<email>     (redirected from forgot-password page)
  const urlToken = searchParams.get('token') || '';
  const emailFromUrl = searchParams.get('email') || '';

  // If a token link was clicked, pre-fill it in the code box for display,
  // but we'll send it as `token` not `otp_code`.
  const isTokenMode = Boolean(urlToken && !emailFromUrl);

  useEffect(() => {
    // If the user landed via the email link (?token=…), pre-fill the token
    // into the OTP field so they don't have to copy-paste it manually.
    if (urlToken && urlToken.length <= 6) setOtpCode(urlToken);
  }, [urlToken]);

  const handleResend = async () => {
    if (!emailFromUrl) return;
    setResending(true);
    try {
      await forgotPassword({ email: emailFromUrl });
      toast({ title: 'Code resent', description: `A new 6-digit code has been sent to ${emailFromUrl}.` });
    } catch {
      toast({ variant: 'destructive', title: 'Could not resend', description: 'Please go back and try again.' });
    } finally {
      setResending(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      toast({ variant: 'destructive', title: "Passwords don't match", description: 'Make sure both password fields match.' });
      return;
    }
    if (password.length < 6) {
      toast({ variant: 'destructive', title: 'Password too short', description: 'Password must be at least 6 characters.' });
      return;
    }

    // Decide whether to send the OTP code or the long URL token
    const payload = isTokenMode
      ? { token: urlToken, password }
      : { otp_code: otpCode.trim(), password };

    if (!payload.token && !payload.otp_code) {
      toast({ variant: 'destructive', title: 'Enter your code', description: 'Please enter the 6-digit code from your email.' });
      return;
    }
    if (payload.otp_code && payload.otp_code.length !== 6) {
      toast({ variant: 'destructive', title: 'Incomplete code', description: 'The reset code is exactly 6 digits.' });
      return;
    }

    setLoading(true);
    try {
      await resetPassword(payload);
      setSuccess(true);
      toast({ title: 'Password updated!', description: 'You can now log in with your new password.' });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Reset failed',
        description: error.message || 'The code may be expired or incorrect. Request a new one.',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Helmet>
        <title>Reset Password — MediGuard</title>
        <meta name="description" content="Enter your reset code and create a new MediGuard password." />
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
                <img src="/mediguard.png" alt="MediGuard Logo" className="logo-md" />
              </div>
              <CardTitle className="text-2xl font-bold">
                {success ? 'Password Updated!' : 'Enter Reset Code'}
              </CardTitle>
              <CardDescription>
                {success
                  ? 'Your password has been changed successfully.'
                  : emailFromUrl
                    ? <>We sent a 6-digit code to <strong>{emailFromUrl}</strong></>
                    : 'Enter the 6-digit code from your email and your new password.'
                }
              </CardDescription>
            </CardHeader>

            <CardContent className="pt-6">
              {success ? (
                <div className="text-center space-y-6 py-4">
                  <div className="bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 p-5 rounded-xl">
                    <KeyRound className="h-10 w-10 mx-auto mb-3" />
                    <p className="font-semibold text-base">Password successfully updated!</p>
                    <p className="text-sm mt-1 opacity-80">You can now log in with your new password.</p>
                  </div>
                  <Button className="w-full h-11 text-base" onClick={() => navigate('/login')}>
                    Go to Login <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-5">

                  {/* OTP code entry — shown unless we're in token-link mode */}
                  {!isTokenMode && (
                    <div className="space-y-3">
                      <Label className="block text-center font-medium">Reset Code</Label>
                      <OtpInput value={otpCode} onChange={setOtpCode} />
                      <p className="text-xs text-center text-muted-foreground">
                        Enter the 6-digit code from your email
                      </p>
                    </div>
                  )}

                  {/* Token-link mode: subtle indicator */}
                  {isTokenMode && (
                    <div className="flex items-center gap-2 bg-primary/8 border border-primary/20 rounded-lg px-4 py-3">
                      <Mail className="h-4 w-4 text-primary shrink-0" />
                      <p className="text-xs text-muted-foreground">
                        Reset link verified — set your new password below.
                      </p>
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label htmlFor="password">New Password</Label>
                    <Input
                      id="password"
                      type="password"
                      placeholder="At least 6 characters"
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
                      placeholder="Repeat your password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                      className="bg-white text-gray-900 dark:bg-slate-900 dark:text-gray-100 focus:ring-primary"
                    />
                  </div>

                  <Button
                    type="submit"
                    className="w-full h-11 text-base transition-transform active:scale-[0.98]"
                    disabled={loading || !password || !confirmPassword || (!isTokenMode && otpCode.length < 6)}
                  >
                    {loading ? 'Updating…' : 'Set New Password'}
                  </Button>

                  {/* Resend link — only when we know the email */}
                  {emailFromUrl && !isTokenMode && (
                    <div className="text-center pt-1">
                      <button
                        type="button"
                        onClick={handleResend}
                        disabled={resending}
                        className="text-sm text-muted-foreground hover:text-primary transition-colors inline-flex items-center gap-1"
                      >
                        <RefreshCw className={`h-3.5 w-3.5 ${resending ? 'animate-spin' : ''}`} />
                        {resending ? 'Sending…' : "Didn't receive a code? Resend"}
                      </button>
                    </div>
                  )}

                  <div className="text-center">
                    <Link
                      to="/forgot-password"
                      className="text-sm text-muted-foreground hover:text-primary transition-colors"
                    >
                      ← Use a different email address
                    </Link>
                  </div>
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
