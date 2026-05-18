import React, { useCallback, useEffect, useState } from 'react';
import { Helmet } from 'react-helmet';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  Trash2, History, MessageSquare, Activity, Calendar, RefreshCw, Search,
  ChevronDown, ChevronRight, Stethoscope, Bot, Clock, TrendingUp, FileText,
  AlertCircle, BookOpen, ExternalLink,
} from 'lucide-react';
import { useAuth } from '@/components/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { deleteChatHistory, deleteHistory, getChatHistory, getHistory } from '@/services/api';

// ─── Animation Variants ───────────────────────────────────────────────────────

const pageVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, staggerChildren: 0.08 } },
};

const cardVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.98 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { type: 'spring', stiffness: 260, damping: 24 } },
};

const StatCard = ({ icon: Icon, label, value, color }) => (
  <motion.div
    variants={cardVariants}
    whileHover={{ y: -3, transition: { duration: 0.2 } }}
    className="rounded-xl border bg-background p-4 shadow-sm"
  >
    <div className={`w-10 h-10 rounded-full flex items-center justify-center mb-3 ${color}`}>
      <Icon className="h-5 w-5 text-white" />
    </div>
    <motion.div
      initial={{ opacity: 0, scale: 0.5 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20, delay: 0.2 }}
      className="text-2xl font-bold text-foreground"
    >
      {value}
    </motion.div>
    <p className="text-xs text-muted-foreground mt-1">{label}</p>
  </motion.div>
);

// ─── Component ────────────────────────────────────────────────────────────────

const HistoryPage = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

  const [symptomChecks, setSymptomChecks] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');
  const [expandedCheck, setExpandedCheck] = useState(null);
  const [expandedChat, setExpandedChat] = useState(null);

  const readLocalArray = (key) => {
    try {
      const value = JSON.parse(localStorage.getItem(key) || '[]');
      return Array.isArray(value) ? value : [];
    } catch { return []; }
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
    const [checksResult, chatsResult] = await Promise.allSettled([getHistory(), getChatHistory()]);
    const remoteChecks = checksResult.status === 'fulfilled' && Array.isArray(checksResult.value.data) ? checksResult.value.data : [];
    const remoteChats = chatsResult.status === 'fulfilled' && Array.isArray(chatsResult.value.data) ? chatsResult.value.data : [];
    setSymptomChecks(mergeNewest(remoteChecks, localChecks, normalizeCheck));
    setChatHistory(mergeNewest(remoteChats, localChats, normalizeChat));
    if (showToast) {
      toast({ title: 'History refreshed', description: 'Latest records loaded.' });
    }
    setLoading(false);
    setRefreshing(false);
  }, [user?.id, toast]);

  useEffect(() => { loadHistory(false); }, [loadHistory]);

  const handleDeleteCheck = async (id) => {
    try { await deleteHistory(id); } catch { /* fallthrough */ }
    const updated = symptomChecks.filter(c => c.id !== id);
    setSymptomChecks(updated);
    const localOnly = updated.filter(c => String(c.id).startsWith('diagnosis_') || String(c.id).startsWith('check_'));
    localStorage.setItem(`symptom_checks_${user.id}`, JSON.stringify(localOnly));
    toast({ title: 'Record deleted' });
  };

  const handleDeleteChat = async (id) => {
    try { await deleteChatHistory(id); } catch { /* fallthrough */ }
    const updated = chatHistory.filter(c => c.id !== id);
    setChatHistory(updated);
    const localOnly = updated.filter(c => String(c.id).startsWith('chat_'));
    localStorage.setItem(`chat_history_${user.id}`, JSON.stringify(localOnly));
    toast({ title: 'Chat deleted' });
  };

  const formatDate = (iso) => {
    const d = new Date(iso);
    const now = new Date();
    const diffDays = Math.floor((now - d) / 86400000);
    if (diffDays === 0) return `Today at ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    if (diffDays === 1) return `Yesterday at ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    return d.toLocaleDateString([], { day: 'numeric', month: 'short', year: 'numeric' });
  };

  const filteredChecks = symptomChecks.filter(c =>
    !search || c.symptoms.some(s => s.toLowerCase().includes(search.toLowerCase())) ||
    c.results.some(r => (r.name || r.disease || '').toLowerCase().includes(search.toLowerCase()))
  );

  const filteredChats = chatHistory.filter(c =>
    !search || c.title?.toLowerCase().includes(search.toLowerCase()) ||
    c.message?.toLowerCase().includes(search.toLowerCase())
  );

  const mostCommonDisease = (() => {
    const counts = {};
    symptomChecks.forEach(c => c.results.slice(0, 1).forEach(r => {
      const n = r.name || r.disease || 'Unknown';
      counts[n] = (counts[n] || 0) + 1;
    }));
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    return sorted[0]?.[0] || 'None';
  })();

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-12 h-12 rounded-full border-4 border-primary/30 border-t-primary"
        />
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-sm text-muted-foreground"
        >
          Loading your health history…
        </motion.p>
      </div>
    );
  }

  return (
    <>
      <Helmet>
        <title>My Health History - MediGuard Bamenda</title>
        <meta name="description" content="View your past symptom checks and AI chat conversations." />
      </Helmet>

      <div className="min-h-screen bg-[linear-gradient(180deg,hsl(var(--muted)/0.4),hsl(var(--background))_30%)] py-10">
        <motion.div
          className="container mx-auto px-4 max-w-5xl"
          variants={pageVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Header */}
          <motion.div variants={cardVariants} className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
            <div className="flex items-center gap-4">
              <motion.div
                animate={{ rotate: [0, -8, 8, 0] }}
                transition={{ duration: 3, repeat: Infinity, repeatDelay: 2 }}
                className="bg-primary/10 p-3 rounded-2xl"
              >
                <History className="h-8 w-8 text-primary" />
              </motion.div>
              <div>
                <h1 className="text-3xl font-bold text-foreground">Health History</h1>
                <p className="text-muted-foreground text-sm mt-0.5">
                  {user ? `Logged in as ${user.full_name || user.email}` : 'Guest — login to sync across devices'}
                </p>
              </div>
            </div>
            <Button variant="outline" onClick={() => loadHistory(true)} disabled={refreshing} className="gap-2 shrink-0">
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </motion.div>

          {/* Stats */}
          <motion.div variants={cardVariants} className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
            <StatCard icon={Activity} label="Symptom Checks" value={symptomChecks.length} color="bg-primary" />
            <StatCard icon={MessageSquare} label="Chat Sessions" value={chatHistory.length} color="bg-secondary" />
            <StatCard icon={TrendingUp} label="Most Common" value={mostCommonDisease.split(' ')[0]} color="bg-orange-500" />
            <StatCard icon={Clock} label="Last Check" value={symptomChecks[0] ? formatDate(symptomChecks[0].created_at).split(' ')[0] : '—'} color="bg-emerald-500" />
          </motion.div>

          {/* Search */}
          <motion.div variants={cardVariants} className="relative mb-6">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search symptoms, diseases, or conversations…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="pl-10 h-11 bg-background shadow-sm"
            />
          </motion.div>

          {/* Guest notice */}
          {!user && (
            <motion.div variants={cardVariants} className="mb-6 p-4 rounded-xl border border-amber-200 bg-amber-50 dark:bg-amber-950/20 flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-amber-800 dark:text-amber-300">You're viewing local records only</p>
                <p className="text-xs text-amber-700 dark:text-amber-400 mt-0.5">
                  <button onClick={() => navigate('/login')} className="underline font-medium">Log in</button> to sync and view your full history across devices.
                </p>
              </div>
            </motion.div>
          )}

          {/* Tabs */}
          <motion.div variants={cardVariants}>
            <Tabs defaultValue="checks">
              <TabsList className="w-full mb-6 h-12 rounded-xl bg-muted">
                <TabsTrigger value="checks" className="flex-1 gap-2 rounded-lg data-[state=active]:shadow-sm">
                  <Activity className="h-4 w-4" />
                  Symptom Checks
                  {filteredChecks.length > 0 && (
                    <Badge variant="secondary" className="ml-1 text-xs">{filteredChecks.length}</Badge>
                  )}
                </TabsTrigger>
                <TabsTrigger value="chats" className="flex-1 gap-2 rounded-lg data-[state=active]:shadow-sm">
                  <MessageSquare className="h-4 w-4" />
                  Chat History
                  {filteredChats.length > 0 && (
                    <Badge variant="secondary" className="ml-1 text-xs">{filteredChats.length}</Badge>
                  )}
                </TabsTrigger>
              </TabsList>

              {/* ── Symptom Checks ─────────────────────────────────────────── */}
              <TabsContent value="checks">
                <AnimatePresence mode="popLayout">
                  {filteredChecks.length === 0 ? (
                    <motion.div key="empty-checks" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                      <EmptyState
                        icon={Stethoscope}
                        title="No symptom checks yet"
                        description="Use the Symptom Checker to assess your health — results will appear here."
                        action={{ label: 'Start Symptom Check', onClick: () => navigate('/symptom-checker') }}
                      />
                    </motion.div>
                  ) : (
                    <motion.div key="checks-list" className="space-y-4" variants={pageVariants} initial="hidden" animate="visible">
                      {filteredChecks.map((check) => (
                        <CheckCard
                          key={check.id}
                          check={check}
                          isExpanded={expandedCheck === check.id}
                          onToggle={() => setExpandedCheck(expandedCheck === check.id ? null : check.id)}
                          onDelete={() => handleDeleteCheck(check.id)}
                          formatDate={formatDate}
                          navigate={navigate}
                        />
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </TabsContent>

              {/* ── Chat History ───────────────────────────────────────────── */}
              <TabsContent value="chats">
                <AnimatePresence mode="popLayout">
                  {filteredChats.length === 0 ? (
                    <motion.div key="empty-chats" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                      <EmptyState
                        icon={Bot}
                        title="No conversations yet"
                        description="Chat with MediGuard AI to get health guidance — your sessions will appear here."
                        action={{ label: 'Open Chat AI', onClick: () => navigate('/chat-ai') }}
                      />
                    </motion.div>
                  ) : (
                    <motion.div key="chats-list" className="space-y-4" variants={pageVariants} initial="hidden" animate="visible">
                      {filteredChats.map((chat) => (
                        <ChatCard
                          key={chat.id}
                          chat={chat}
                          isExpanded={expandedChat === chat.id}
                          onToggle={() => setExpandedChat(expandedChat === chat.id ? null : chat.id)}
                          onDelete={() => handleDeleteChat(chat.id)}
                          formatDate={formatDate}
                          navigate={navigate}
                        />
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </TabsContent>
            </Tabs>
          </motion.div>
        </motion.div>
      </div>
    </>
  );
};

// ─── Sub-components ───────────────────────────────────────────────────────────

const EmptyState = ({ icon: Icon, title, description, action }) => (
  <motion.div
    initial={{ opacity: 0, scale: 0.95 }}
    animate={{ opacity: 1, scale: 1 }}
    className="flex flex-col items-center justify-center py-20 text-center"
  >
    <motion.div
      animate={{ y: [0, -8, 0] }}
      transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
      className="w-20 h-20 rounded-full bg-muted flex items-center justify-center mb-4"
    >
      <Icon className="h-10 w-10 text-muted-foreground/50" />
    </motion.div>
    <h3 className="text-lg font-semibold text-foreground mb-1">{title}</h3>
    <p className="text-sm text-muted-foreground max-w-xs mb-5">{description}</p>
    {action && (
      <Button onClick={action.onClick} className="gap-2">
        {action.label}
        <ChevronRight className="h-4 w-4" />
      </Button>
    )}
  </motion.div>
);

const CheckCard = ({ check, isExpanded, onToggle, onDelete, formatDate, navigate }) => {
  const topResult = check.results[0];
  const severityColor = topResult?.severity === 'High' ? 'text-red-600' : topResult?.severity === 'Medium' ? 'text-yellow-600' : 'text-green-600';

  return (
    <motion.div
      variants={cardVariants}
      whileHover={{ y: -2 }}
      layout
    >
      <Card className="overflow-hidden border-border/60 shadow-sm hover:shadow-md transition-shadow">
        {/* Card header — always visible */}
        <div
          className="flex items-start justify-between gap-3 p-4 cursor-pointer select-none"
          onClick={onToggle}
        >
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
              <Activity className="h-5 w-5 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap mb-1">
                {topResult && (
                  <Badge variant="outline" className={`text-xs font-semibold ${severityColor}`}>
                    {topResult.name || topResult.disease || 'Unknown'}
                    {(topResult.confidence ?? topResult.probability) != null && ` · ${topResult.confidence ?? topResult.probability}%`}
                  </Badge>
                )}
                {check.results.length > 1 && (
                  <span className="text-xs text-muted-foreground">+{check.results.length - 1} more</span>
                )}
              </div>
              <div className="flex flex-wrap gap-1">
                {check.symptoms.slice(0, 5).map(s => (
                  <Badge key={s} variant="secondary" className="text-[10px] py-0">{s}</Badge>
                ))}
                {check.symptoms.length > 5 && (
                  <Badge variant="secondary" className="text-[10px] py-0">+{check.symptoms.length - 5}</Badge>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-xs text-muted-foreground hidden sm:block">{formatDate(check.created_at)}</span>
            <motion.div animate={{ rotate: isExpanded ? 180 : 0 }} transition={{ duration: 0.2 }}>
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            </motion.div>
            <Button
              variant="ghost" size="icon" className="h-7 w-7 text-destructive/70 hover:text-destructive"
              onClick={(e) => { e.stopPropagation(); onDelete(); }}
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>

        {/* Expandable detail */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="overflow-hidden"
            >
              <div className="border-t bg-muted/20 p-4 space-y-4">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Calendar className="h-3.5 w-3.5" />
                  {new Date(check.created_at).toLocaleString()}
                </div>

                <div>
                  <p className="text-xs font-semibold text-muted-foreground mb-2">ALL REPORTED SYMPTOMS</p>
                  <div className="flex flex-wrap gap-1.5">
                    {check.symptoms.map(s => (
                      <Badge key={s} variant="outline" className="text-xs bg-background">{s}</Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-xs font-semibold text-muted-foreground mb-2">TOP PREDICTIONS</p>
                  <div className="space-y-2">
                    {check.results.slice(0, 3).map((r, i) => {
                      const confidence = r.confidence ?? r.probability ?? 0;
                      return (
                        <div key={r.id || r.slug || r.name || i} className="flex items-center gap-3">
                          <span className={`text-xs font-bold w-4 ${i === 0 ? 'text-primary' : 'text-muted-foreground'}`}>#{i + 1}</span>
                          <div className="flex-1">
                            <div className="flex justify-between text-sm mb-0.5">
                              <span className="font-medium">{r.name || r.disease || 'Unknown'}</span>
                              <span className="text-muted-foreground text-xs">{confidence}%</span>
                            </div>
                            <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                              <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${confidence}%` }}
                                transition={{ duration: 0.6, delay: i * 0.1 }}
                                className={`h-full rounded-full ${confidence >= 70 ? 'bg-green-500' : confidence >= 40 ? 'bg-yellow-500' : 'bg-gray-400'}`}
                              />
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="flex gap-2 pt-2">
                  {topResult && (
                    <Button size="sm" variant="outline" className="gap-1.5 text-xs"
                      onClick={() => navigate(`/disease/${topResult.id || topResult.slug}`)}>
                      <BookOpen className="h-3.5 w-3.5" />View Disease Info
                    </Button>
                  )}
                  <Button size="sm" variant="outline" className="gap-1.5 text-xs"
                    onClick={() => navigate('/symptom-checker')}>
                    <Activity className="h-3.5 w-3.5" />New Check
                  </Button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </Card>
    </motion.div>
  );
};

const ChatCard = ({ chat, isExpanded, onToggle, onDelete, formatDate, navigate }) => (
  <motion.div variants={cardVariants} whileHover={{ y: -2 }} layout>
    <Card className="overflow-hidden border-border/60 shadow-sm hover:shadow-md transition-shadow">
      <div
        className="flex items-start justify-between gap-3 p-4 cursor-pointer select-none"
        onClick={onToggle}
      >
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <div className="w-10 h-10 rounded-full bg-secondary/10 flex items-center justify-center shrink-0 mt-0.5">
            <Bot className="h-5 w-5 text-secondary" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-foreground truncate">{chat.title}</p>
            <p className="text-xs text-muted-foreground truncate mt-0.5">{chat.message}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-muted-foreground hidden sm:block">{formatDate(chat.created_at)}</span>
          <motion.div animate={{ rotate: isExpanded ? 180 : 0 }} transition={{ duration: 0.2 }}>
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          </motion.div>
          <Button
            variant="ghost" size="icon" className="h-7 w-7 text-destructive/70 hover:text-destructive"
            onClick={(e) => { e.stopPropagation(); onDelete(); }}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="border-t bg-muted/20 p-4 space-y-3">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Calendar className="h-3.5 w-3.5" />{new Date(chat.created_at).toLocaleString()}
              </div>

              <div className="bg-primary/5 border border-primary/20 p-3 rounded-lg">
                <span className="text-xs font-bold text-primary block mb-1">YOU ASKED</span>
                <p className="text-sm text-foreground">{chat.message}</p>
              </div>
              <div className="bg-muted/40 border p-3 rounded-lg">
                <span className="text-xs font-bold text-muted-foreground block mb-1">MEDIGUARD AI</span>
                <p className="text-sm text-foreground line-clamp-4">{chat.response}</p>
              </div>

              {chat.sources?.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  <span className="text-xs text-muted-foreground mr-1">Sources:</span>
                  {chat.sources.map(s => (
                    <Badge key={s} variant="outline" className="text-[10px]">{s}</Badge>
                  ))}
                </div>
              )}

              <div className="flex gap-2 pt-1">
                <Button size="sm" variant="outline" className="gap-1.5 text-xs"
                  onClick={() => navigate('/chat-ai')}>
                  <ExternalLink className="h-3.5 w-3.5" />Continue in Chat
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  </motion.div>
);

export default HistoryPage;
