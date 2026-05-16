import React, { useEffect, useState } from 'react';
import { Helmet } from 'react-helmet';
import { Link } from 'react-router-dom';
import { Activity, Bot, Calendar, Mail, ShieldCheck, User } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/components/AuthContext';
import { getChatHistory, getHistory, getMe } from '@/services/api';

const ProfilePage = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState(user);
  const [stats, setStats] = useState({
    symptomChecks: 0,
    chatMessages: 0,
    lastActivity: null,
  });

  useEffect(() => {
    getMe()
      .then((res) => setProfile(res.data))
      .catch(() => setProfile(user));

    Promise.allSettled([getHistory(), getChatHistory()]).then(([checks, chats]) => {
      const symptomRows = checks.status === 'fulfilled' && Array.isArray(checks.value.data) ? checks.value.data : [];
      const chatRows = chats.status === 'fulfilled' && Array.isArray(chats.value.data) ? chats.value.data : [];
      const dates = [...symptomRows, ...chatRows]
        .map((item) => item.created_at)
        .filter(Boolean)
        .sort()
        .reverse();

      setStats({
        symptomChecks: symptomRows.length,
        chatMessages: chatRows.length,
        lastActivity: dates[0] || null,
      });
    });
  }, [user]);

  const displayName = profile?.full_name || profile?.username || 'MediGuard User';
  const joinedDate = profile?.created_at ? new Date(profile.created_at).toLocaleDateString() : 'Not available';
  const lastActivity = stats.lastActivity ? new Date(stats.lastActivity).toLocaleString() : 'No activity yet';

  return (
    <>
      <Helmet>
        <title>My Profile - MediGuard Bamenda</title>
        <meta name="description" content="View your MediGuard account profile and activity summary." />
      </Helmet>

      <div className="min-h-screen medical-page py-8 sm:py-12">
        <div className="container mx-auto px-4 max-w-5xl">
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
            <Card className="medical-panel lg:col-span-2">
              <CardHeader>
                <CardTitle>Account Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
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
              </CardContent>
            </Card>

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
        </div>
      </div>
    </>
  );
};

export default ProfilePage;
