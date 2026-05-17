
import React, { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Trash2, History, MessageSquare, Activity, Calendar, RefreshCw } from 'lucide-react';
import { useAuth } from '@/components/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { deleteChatHistory, deleteHistory, getChatHistory, getHistory } from '@/services/api';

const HistoryPage = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [symptomChecks, setSymptomChecks] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const readLocalArray = (key) => {
    try {
      const value = JSON.parse(localStorage.getItem(key) || '[]');
      return Array.isArray(value) ? value : [];
    } catch {
      return [];
    }
  };

  const normalizeCheck = (check) => ({
    ...check,
    id: check.id ?? check.prediction_log_id ?? `check_${Date.now()}`,
    symptoms: Array.isArray(check.symptoms) ? check.symptoms : [],
    results: Array.isArray(check.results) ? check.results : (Array.isArray(check.predictions) ? check.predictions : []),
    created_at: check.created_at || check.timestamp || new Date().toISOString(),
  });

  const normalizeChat = (chat) => ({
    ...chat,
    title: chat.title || 'MediGuard AI Chat',
    message: chat.message || '',
    response: chat.response || '',
    sources: Array.isArray(chat.sources) ? chat.sources : [],
    follow_up_questions: Array.isArray(chat.follow_up_questions) ? chat.follow_up_questions : [],
    created_at: chat.created_at || chat.timestamp || new Date().toISOString(),
  });

  const mergeNewest = (remoteItems, localItems, normalize) => {
    const seen = new Set();
    return [...remoteItems, ...localItems]
      .map(normalize)
      .filter((item) => {
        const key = `${item.id}-${item.created_at}-${item.message || item.top_disease || ''}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  };

  const loadHistory = useCallback(async (showToast = false) => {
    if (!user?.id) {
      setSymptomChecks([]);
      setChatHistory([]);
      setLoading(false);
      return;
    }

    setRefreshing(true);
    const localChecks = readLocalArray(`symptom_checks_${user.id}`);
    const localChats = readLocalArray(`chat_history_${user.id}`);

    const [checksResult, chatsResult] = await Promise.allSettled([
      getHistory(),
      getChatHistory(),
    ]);

    const remoteChecks = checksResult.status === 'fulfilled' && Array.isArray(checksResult.value.data)
      ? checksResult.value.data
      : [];
    const remoteChats = chatsResult.status === 'fulfilled' && Array.isArray(chatsResult.value.data)
      ? chatsResult.value.data
      : [];

    setSymptomChecks(mergeNewest(remoteChecks, localChecks, normalizeCheck));
    setChatHistory(mergeNewest(remoteChats, localChats, normalizeChat));

    if (showToast) {
      if (checksResult.status === 'fulfilled' && chatsResult.status === 'fulfilled') {
        toast({ title: 'History refreshed', description: 'Latest symptom checks and chats loaded.' });
      } else {
        toast({
          title: 'History partially loaded',
          description: 'Some online history could not be fetched, so local saved records were shown too.',
          variant: 'destructive',
        });
      }
    }

    setLoading(false);
    setRefreshing(false);
  }, [user?.id, toast]);

  useEffect(() => {
    loadHistory(false);
  }, [loadHistory]);

  const handleDeleteCheck = async (id) => {
    try {
      await deleteHistory(id);
    } catch {
      // Local fallback records are still removed below.
    }
    const updated = symptomChecks.filter(check => check.id !== id);
    setSymptomChecks(updated);
    const localOnly = updated.filter(check => String(check.id).startsWith('diagnosis_') || String(check.id).startsWith('check_'));
    localStorage.setItem(`symptom_checks_${user.id}`, JSON.stringify(localOnly));
    toast({ title: "Record Deleted", description: "Symptom check removed from history." });
  };

  const handleDeleteChat = async (id) => {
    try {
      await deleteChatHistory(id);
    } catch {
      // Local fallback records are still removed below.
    }
    const updated = chatHistory.filter(chat => chat.id !== id);
    setChatHistory(updated);
    const localOnly = updated.filter(chat => String(chat.id).startsWith('chat_'));
    localStorage.setItem(`chat_history_${user.id}`, JSON.stringify(localOnly));
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
              <Button variant="outline" onClick={() => loadHistory(true)} disabled={refreshing} className="gap-2">
                <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
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
                            {check.results.slice(0, 3).map((res, index) => (
                              <Badge key={res.id || res.slug || res.name || res.disease || index} variant={res.severity?.toLowerCase() === 'high' ? 'destructive' : 'secondary'}>
                                {res.name || res.disease || 'Unknown'} ({res.confidence ?? res.probability ?? 0}%)
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
                        {Array.isArray(chat.sources) && chat.sources.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {chat.sources.map((source) => (
                              <Badge key={source} variant="outline" className="text-xs">
                                {source}
                              </Badge>
                            ))}
                          </div>
                        )}
                        {chat.follow_up_questions.length > 0 && (
                          <div>
                            <span className="text-xs font-semibold text-muted-foreground">Follow-up questions asked:</span>
                            <div className="mt-1 flex flex-wrap gap-1">
                              {chat.follow_up_questions.map((question) => (
                                <Badge key={question} variant="outline" className="text-xs">
                                  {question}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
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
