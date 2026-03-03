
import React, { useState, useEffect } from 'react';
import { Helmet } from 'react-helmet';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Trash2, History, MessageSquare, Activity, Calendar } from 'lucide-react';
import { useAuth } from '@/components/AuthContext';
import { useToast } from '@/hooks/use-toast';

const HistoryPage = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [symptomChecks, setSymptomChecks] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadHistory = () => {
      const storedChecks = JSON.parse(localStorage.getItem(`symptom_checks_${user?.id}`) || '[]');
      const storedChats = JSON.parse(localStorage.getItem(`chat_history_${user?.id}`) || '[]');
      
      setSymptomChecks(storedChecks);
      setChatHistory(storedChats);
      setLoading(false);
    };

    if (user) {
      loadHistory();
    }
  }, [user]);

  const handleDeleteCheck = (id) => {
    const updated = symptomChecks.filter(check => check.id !== id);
    setSymptomChecks(updated);
    localStorage.setItem(`symptom_checks_${user.id}`, JSON.stringify(updated));
    toast({ title: "Record Deleted", description: "Symptom check removed from history." });
  };

  const handleDeleteChat = (id) => {
    const updated = chatHistory.filter(chat => chat.id !== id);
    setChatHistory(updated);
    localStorage.setItem(`chat_history_${user.id}`, JSON.stringify(updated));
    toast({ title: "Record Deleted", description: "Chat conversation removed from history." });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <>
      <Helmet>
        <title>My Health History - MediGuard Bamenda</title>
        <meta name="description" content="View your past symptom checks and AI chat conversations." />
      </Helmet>

      <div className="min-h-screen bg-muted/30 py-12">
        <div className="container mx-auto px-4 max-w-5xl">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
            <div className="flex items-center gap-3">
              <div className="bg-primary/10 p-3 rounded-full">
                <History className="h-8 w-8 text-primary" />
              </div>
              <div>
                <h1 className="text-4xl font-bold">My Health History</h1>
                <p className="text-lg text-muted-foreground">
                  Review your past AI assessments and conversations
                </p>
              </div>
            </div>

            <div className="hidden sm:block">
              <img 
                src="/public/mediguard.png" 
                alt="MediGuard Logo" 
                className="logo-sm"
              />
            </div>
          </div>

          <div className="space-y-8">
            <section>
              <h2 className="text-2xl font-bold flex items-center gap-2 mb-4">
                <Activity className="h-6 w-6 text-primary" />
                Symptom Checks
              </h2>
              {symptomChecks.length === 0 ? (
                <Card className="border-dashed">
                  <CardContent className="py-12 text-center text-muted-foreground">
                    No symptom checks recorded yet.
                  </CardContent>
                </Card>
              ) : (
                <div className="grid gap-4">
                  {symptomChecks.map((check) => (
                    <Card key={check.id}>
                      <CardHeader className="pb-2 border-b">
                        <div className="flex justify-between items-start">
                          <div className="flex items-center gap-2 text-muted-foreground text-sm">
                            <Calendar className="h-4 w-4" />
                            {new Date(check.created_at).toLocaleString()}
                          </div>
                          <Button variant="ghost" size="icon" className="text-destructive" onClick={() => handleDeleteCheck(check.id)}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent className="pt-4">
                        <div className="mb-3">
                          <span className="text-sm font-semibold block mb-1">Symptoms Reported:</span>
                          <div className="flex flex-wrap gap-1">
                            {check.symptoms.map(s => (
                              <Badge key={s} variant="outline" className="text-xs bg-muted">
                                {s}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        <div>
                          <span className="text-sm font-semibold block mb-1">Top Predictions:</span>
                          <div className="flex flex-wrap gap-2">
                            {check.results.slice(0, 3).map(res => (
                              <Badge key={res.id} variant={res.severity?.toLowerCase() === 'high' ? 'destructive' : 'secondary'}>
                                {res.name} ({res.confidence}%)
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </section>

            <section>
              <h2 className="text-2xl font-bold flex items-center gap-2 mb-4">
                <MessageSquare className="h-6 w-6 text-primary" />
                Chat Conversations
              </h2>
              {chatHistory.length === 0 ? (
                <Card className="border-dashed">
                  <CardContent className="py-12 text-center text-muted-foreground">
                    No chat history recorded yet.
                  </CardContent>
                </Card>
              ) : (
                <div className="grid gap-4">
                  {chatHistory.map((chat) => (
                    <Card key={chat.id}>
                      <CardHeader className="pb-2 border-b">
                        <div className="flex justify-between items-start">
                          <div className="flex items-center gap-2 text-muted-foreground text-sm">
                            <Calendar className="h-4 w-4" />
                            {new Date(chat.created_at).toLocaleString()}
                          </div>
                          <Button variant="ghost" size="icon" className="text-destructive" onClick={() => handleDeleteChat(chat.id)}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent className="pt-4 space-y-3">
                        <div className="bg-primary/10 text-foreground p-3 rounded-lg text-sm border">
                          <span className="font-semibold block mb-1 text-primary">You:</span>
                          {chat.message}
                        </div>
                        <div className="bg-muted text-foreground p-3 rounded-lg text-sm border">
                          <span className="font-semibold block mb-1 text-secondary-foreground">MediGuard AI:</span>
                          {chat.response}
                        </div>
                        {chat.gender_context && (
                          <div className="text-xs text-muted-foreground mt-2">
                            <span className="font-semibold">Context Info:</span> AI adjusted response based on gender profile ({chat.gender_context}).
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </section>
          </div>
        </div>
      </div>
    </>
  );
};

export default HistoryPage;
