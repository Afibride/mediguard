import React, { useEffect, useState } from 'react';
import { Helmet } from 'react-helmet';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Bot, Calendar, Mail, ShieldCheck, User, Bell, BellOff, Pencil, KeyRound, Check, X, Eye, EyeOff } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/components/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { changePassword, getChatHistory, getHistory, getMe, updateNotificationPrefs, updateProfile } from '@/services/api';

const ProfilePage = () => {
  const { user, updateUser } = useAuth();
  const { toast } = useToast();
  const [profile, setProfile] = useState(user);
  const [stats, setStats] = useState({ symptomChecks: 0, chatMessages: 0, lastActivity: null });
  const [notifyEmails, setNotifyEmails] = useState(true);
  const [notifySaving, setNotifySaving] = useState(false);

  // Edit profile state
  const [editingProfile, setEditingProfile] = useState(false);
  const [editName, setEditName] = useState('');
  const [editEmail, setEditEmail] = useState('');
  const [profileSaving, setProfileSaving] = useState(false);

  // Change password state
  const [changingPassword, setChangingPassword] = useState(false);
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [showCurrentPw, setShowCurrentPw] = useState(false);
  const [showNewPw, setShowNewPw] = useState(false);
  const [pwSaving, setPwSaving] = useState(false);

  useEffect(() => {
    getMe()
      .then((res) => {
        setProfile(res.data);
        setNotifyEmails(res.data.notify_emails !== false);
      })
      .catch(() => setProfile(user));

    Promise.allSettled([getHistory(), getChatHistory()]).then(([checks, chats]) => {
      const symptomRows = checks.status === 'fulfilled' && Array.isArray(checks.value.data) ? checks.value.data : [];
      const chatRows = chats.status === 'fulfilled' && Array.isArray(chats.value.data) ? chats.value.data : [];
      const dates = [...symptomRows, ...chatRows].map(item => item.created_at).filter(Boolean).sort().reverse();
      setStats({ symptomChecks: symptomRows.length, chatMessages: chatRows.length, lastActivity: dates[0] || null });
    });
  }, [user]);

  const openEditProfile = () => {
    setEditName(profile?.full_name || '');
    setEditEmail(profile?.email || '');
    setEditingProfile(true);
    setChangingPassword(false);
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    if (!editName.trim()) return;
    setProfileSaving(true);
    try {
      const payload = {};
      if (editName.trim() !== profile?.full_name) payload.full_name = editName.trim();
      if (editEmail.trim() !== profile?.email) payload.email = editEmail.trim();
      if (Object.keys(payload).length === 0) {
        setEditingProfile(false);
        return;
      }
      const res = await updateProfile(payload);
      setProfile(res.data);
      updateUser(res.data);
      setEditingProfile(false);
      toast({ title: 'Profile updated', description: 'Your details have been saved.' });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Update failed', description: err.message || 'Could not save changes.' });
    } finally {
      setProfileSaving(false);
    }
  };

  const openChangePassword = () => {
    setCurrentPw(''); setNewPw(''); setConfirmPw('');
    setChangingPassword(true);
    setEditingProfile(false);
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    if (newPw !== confirmPw) {
      toast({ variant: 'destructive', title: 'Passwords do not match', description: 'New password and confirmation must be identical.' });
      return;
    }
    if (newPw.length < 6) {
      toast({ variant: 'destructive', title: 'Too short', description: 'New password must be at least 6 characters.' });
      return;
    }
    setPwSaving(true);
    try {
      await changePassword({ current_password: currentPw, new_password: newPw });
      setChangingPassword(false);
      toast({ title: 'Password changed', description: 'Your password has been updated successfully.' });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Change failed', description: err.message || 'Could not change password.' });
    } finally {
      setPwSaving(false);
    }
  };

  const handleToggleNotifications = async (value) => {
    setNotifySaving(true);
    try {
      await updateNotificationPrefs({ notify_emails: value });
      setNotifyEmails(value);
      toast({
        title: value ? 'Notifications enabled' : 'Notifications disabled',
        description: value
          ? 'You will receive outbreak alerts and health tips by email.'
          : 'You will no longer receive health notification emails.',
      });
    } catch {
      toast({ variant: 'destructive', title: 'Could not update preferences', description: 'Please try again.' });
    } finally {
      setNotifySaving(false);
    }
  };

  const displayName = profile?.full_name || profile?.username || 'MediGuard User';
  const joinedDate = profile?.created_at ? new Date(profile.created_at).toLocaleDateString() : 'Not available';
  const lastActivity = stats.lastActivity ? new Date(stats.lastActivity).toLocaleString() : 'No activity yet';

  return (
    <>
      <Helmet>
        <title>My Profile - MediGuard Bamenda</title>
        <meta name="description" content="View and edit your MediGuard account profile." />
      </Helmet>

      <div className="min-h-screen medical-page py-8 sm:py-12">
        <div className="container mx-auto px-4 max-w-5xl">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
            <div className="flex items-center gap-4">
              <div className="h-16 w-16 rounded-full bg-primary/10 text-primary flex items-center justify-center">
                <User className="h-8 w-8" />
              </div>
              <div>
                <h1 className="text-3xl sm:text-4xl font-bold">{displayName}</h1>
                <p className="text-muted-foreground">MediGuard account profile</p>
              </div>
            </div>
            <Badge variant={profile?.is_active === false ? 'destructive' : 'secondary'} className="w-fit">
              <ShieldCheck className="h-3 w-3 mr-1" />
              {profile?.is_active === false ? 'Inactive' : 'Active'}
            </Badge>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-2 sm:gap-4 mb-8">
            {[
              { label: 'Symptom Checks', value: stats.symptomChecks, icon: Activity },
              { label: 'Saved Chats', value: stats.chatMessages, icon: Bot },
              { label: 'Last Activity', value: stats.lastActivity ? 'Recent' : 'None', icon: Calendar },
            ].map((item) => (
              <Card key={item.label} className="medical-panel">
                <CardContent className="p-2.5 sm:p-5 flex flex-col sm:flex-row items-center text-center sm:text-left gap-2 sm:gap-4 min-h-[108px] sm:min-h-0">
                  <div className="h-8 w-8 sm:h-10 sm:w-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
                    <item.icon className="h-4 w-4 sm:h-5 sm:w-5" />
                  </div>
                  <div className="min-w-0 w-full">
                    <p className="text-[10px] sm:text-sm text-muted-foreground leading-tight">{item.label}</p>
                    <p className="text-sm sm:text-2xl font-bold truncate">{item.value}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Account Details / Edit Form */}
            <div className="lg:col-span-2 space-y-4">
              <Card className="medical-panel">
                <CardHeader className="flex flex-row items-center justify-between pb-3">
                  <CardTitle>Account Details</CardTitle>
                  {!editingProfile && !changingPassword && (
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={openEditProfile} className="h-8 gap-1.5">
                        <Pencil className="h-3.5 w-3.5" /> Edit
                      </Button>
                      <Button size="sm" variant="outline" onClick={openChangePassword} className="h-8 gap-1.5">
                        <KeyRound className="h-3.5 w-3.5" /> Password
                      </Button>
                    </div>
                  )}
                </CardHeader>

                <CardContent className="space-y-4">
                  <AnimatePresence mode="wait">
                    {editingProfile ? (
                      <motion.form
                        key="edit-profile"
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -8 }}
                        onSubmit={handleSaveProfile}
                        className="space-y-4"
                      >
                        <div className="space-y-1.5">
                          <Label htmlFor="edit-name">Full Name</Label>
                          <Input
                            id="edit-name"
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                            required
                            minLength={2}
                            placeholder="Your full name"
                          />
                        </div>
                        <div className="space-y-1.5">
                          <Label htmlFor="edit-email">Email</Label>
                          <Input
                            id="edit-email"
                            type="email"
                            value={editEmail}
                            onChange={(e) => setEditEmail(e.target.value)}
                            required
                            placeholder="your@email.com"
                          />
                        </div>
                        <div className="flex gap-2 pt-1">
                          <Button type="submit" size="sm" disabled={profileSaving} className="gap-1.5">
                            <Check className="h-3.5 w-3.5" />
                            {profileSaving ? 'Saving…' : 'Save Changes'}
                          </Button>
                          <Button type="button" size="sm" variant="outline" onClick={() => setEditingProfile(false)} className="gap-1.5">
                            <X className="h-3.5 w-3.5" /> Cancel
                          </Button>
                        </div>
                      </motion.form>
                    ) : changingPassword ? (
                      <motion.form
                        key="change-password"
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -8 }}
                        onSubmit={handleChangePassword}
                        className="space-y-4"
                      >
                        <div className="space-y-1.5">
                          <Label htmlFor="current-pw">Current Password</Label>
                          <div className="relative">
                            <Input
                              id="current-pw"
                              type={showCurrentPw ? 'text' : 'password'}
                              value={currentPw}
                              onChange={(e) => setCurrentPw(e.target.value)}
                              required
                              placeholder="Enter current password"
                              className="pr-10"
                            />
                            <button
                              type="button"
                              onClick={() => setShowCurrentPw(v => !v)}
                              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                            >
                              {showCurrentPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </button>
                          </div>
                        </div>
                        <div className="space-y-1.5">
                          <Label htmlFor="new-pw">New Password</Label>
                          <div className="relative">
                            <Input
                              id="new-pw"
                              type={showNewPw ? 'text' : 'password'}
                              value={newPw}
                              onChange={(e) => setNewPw(e.target.value)}
                              required
                              minLength={6}
                              placeholder="At least 6 characters"
                              className="pr-10"
                            />
                            <button
                              type="button"
                              onClick={() => setShowNewPw(v => !v)}
                              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                            >
                              {showNewPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </button>
                          </div>
                        </div>
                        <div className="space-y-1.5">
                          <Label htmlFor="confirm-pw">Confirm New Password</Label>
                          <Input
                            id="confirm-pw"
                            type="password"
                            value={confirmPw}
                            onChange={(e) => setConfirmPw(e.target.value)}
                            required
                            placeholder="Repeat new password"
                            className={confirmPw && confirmPw !== newPw ? 'border-destructive' : ''}
                          />
                          {confirmPw && confirmPw !== newPw && (
                            <p className="text-xs text-destructive">Passwords do not match</p>
                          )}
                        </div>
                        <div className="flex gap-2 pt-1">
                          <Button type="submit" size="sm" disabled={pwSaving || (confirmPw.length > 0 && confirmPw !== newPw)} className="gap-1.5">
                            <KeyRound className="h-3.5 w-3.5" />
                            {pwSaving ? 'Changing…' : 'Change Password'}
                          </Button>
                          <Button type="button" size="sm" variant="outline" onClick={() => setChangingPassword(false)} className="gap-1.5">
                            <X className="h-3.5 w-3.5" /> Cancel
                          </Button>
                        </div>
                      </motion.form>
                    ) : (
                      <motion.div
                        key="view-profile"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="space-y-4"
                      >
                        <div className="flex items-center gap-3 rounded-lg border bg-background p-4">
                          <User className="h-5 w-5 text-primary" />
                          <div>
                            <p className="text-sm text-muted-foreground">Full Name</p>
                            <p className="font-semibold">{displayName}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3 rounded-lg border bg-background p-4">
                          <Mail className="h-5 w-5 text-primary" />
                          <div>
                            <p className="text-sm text-muted-foreground">Email</p>
                            <p className="font-semibold break-all">{profile?.email}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3 rounded-lg border bg-background p-4">
                          <Calendar className="h-5 w-5 text-primary" />
                          <div>
                            <p className="text-sm text-muted-foreground">Joined</p>
                            <p className="font-semibold">{joinedDate}</p>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </CardContent>
              </Card>
            </div>

            {/* Activity panel */}
            <Card className="medical-panel">
              <CardHeader>
                <CardTitle>Activity</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground">Last Activity</p>
                  <p className="font-semibold">{lastActivity}</p>
                </div>
                <div className="grid gap-3">
                  <Link to="/history">
                    <Button className="w-full">View Full History</Button>
                  </Link>
                  <Link to="/chat-ai">
                    <Button variant="outline" className="w-full">Open Chat AI</Button>
                  </Link>
                  <Link to="/symptom-checker">
                    <Button variant="outline" className="w-full">New Symptom Check</Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Notification Settings */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="mt-6"
          >
            <Card className="medical-panel border-primary/20">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="h-5 w-5 text-primary" />
                  Notification Settings
                </CardTitle>
                <CardDescription>
                  Control which health emails MediGuard sends to <strong>{profile?.email}</strong>
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between rounded-lg border bg-background p-4">
                  <div className="flex items-start gap-3">
                    {notifyEmails
                      ? <Bell className="h-5 w-5 text-primary mt-0.5 shrink-0" />
                      : <BellOff className="h-5 w-5 text-muted-foreground mt-0.5 shrink-0" />
                    }
                    <div>
                      <p className="font-semibold text-sm">Health alert emails</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        Outbreak surveillance alerts, seasonal disease prevention tips, and password reset emails.
                      </p>
                    </div>
                  </div>
                  <Button
                    variant={notifyEmails ? 'default' : 'outline'}
                    size="sm"
                    disabled={notifySaving}
                    onClick={() => handleToggleNotifications(!notifyEmails)}
                    className="shrink-0 ml-4"
                  >
                    {notifySaving ? 'Saving…' : notifyEmails ? 'Enabled' : 'Disabled'}
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground mt-3">
                  Password reset emails are always sent regardless of this setting.
                </p>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </>
  );
};

export default ProfilePage;
