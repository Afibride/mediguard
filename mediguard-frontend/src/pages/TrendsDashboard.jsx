import React, { useEffect, useMemo, useState } from 'react';
import { Helmet } from 'react-helmet';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import {
  TrendingUp, Users, Activity, AlertCircle, ShieldCheck, MapPinned, Database,
  AlertTriangle, Bell, Shield, Droplets, Wind, Thermometer, Bug, ChevronDown, ChevronUp,
  Info, Loader2, Send,
} from 'lucide-react';
import { diseases } from '@/data/diseases';
import { getAnalyticsSummary, getDiseases, getHeatmap, getTopDiseases, getTrends, sendOutbreakAlerts } from '@/services/api';
import { useAuth } from '@/components/AuthContext';
import { useToast } from '@/hooks/use-toast';

// ─── Seasonal fallback data (Bamenda documented patterns) ────────────────────
const SEASONAL_FALLBACK = [
  { month: 'Jan', Malaria: 40, Typhoid: 25, Respiratory: 60, Cholera: 5 },
  { month: 'Feb', Malaria: 45, Typhoid: 28, Respiratory: 55, Cholera: 8 },
  { month: 'Mar', Malaria: 50, Typhoid: 30, Respiratory: 45, Cholera: 12 },
  { month: 'Apr', Malaria: 65, Typhoid: 35, Respiratory: 40, Cholera: 20 },
  { month: 'May', Malaria: 85, Typhoid: 40, Respiratory: 35, Cholera: 25 },
  { month: 'Jun', Malaria: 110, Typhoid: 45, Respiratory: 30, Cholera: 40 },
  { month: 'Jul', Malaria: 130, Typhoid: 50, Respiratory: 35, Cholera: 45 },
  { month: 'Aug', Malaria: 120, Typhoid: 45, Respiratory: 40, Cholera: 35 },
  { month: 'Sep', Malaria: 95, Typhoid: 40, Respiratory: 45, Cholera: 20 },
  { month: 'Oct', Malaria: 70, Typhoid: 35, Respiratory: 50, Cholera: 15 },
  { month: 'Nov', Malaria: 50, Typhoid: 30, Respiratory: 55, Cholera: 10 },
  { month: 'Dec', Malaria: 45, Typhoid: 25, Respiratory: 65, Cholera: 5 },
];

const AGE_GROUP_DATA = [
  { age: '0–10', cases: 380 },
  { age: '11–20', cases: 420 },
  { age: '21–30', cases: 580 },
  { age: '31–40', cases: 540 },
  { age: '41–50', cases: 400 },
  { age: '51–60', cases: 350 },
  { age: '60+', cases: 330 },
];

// ─── Sensitization content ───────────────────────────────────────────────────
const SENSITIZATION = {
  rainy: [
    {
      icon: Bug,
      color: 'text-red-600',
      bg: 'bg-red-50 dark:bg-red-950/20',
      border: 'border-red-200 dark:border-red-800',
      disease: 'Malaria Prevention',
      tip: 'Sleep under insecticide-treated nets every night. Empty or cover containers that collect rainwater — mosquitoes breed in stagnant water within days.',
    },
    {
      icon: Droplets,
      color: 'text-blue-600',
      bg: 'bg-blue-50 dark:bg-blue-950/20',
      border: 'border-blue-200 dark:border-blue-800',
      disease: 'Cholera & Typhoid Prevention',
      tip: 'Drink only boiled, filtered, or treated water. Wash hands with soap and water before eating and after using the toilet. Avoid street food during peak rainy months.',
    },
    {
      icon: Shield,
      color: 'text-green-600',
      bg: 'bg-green-50 dark:bg-green-950/20',
      border: 'border-green-200 dark:border-green-800',
      disease: 'General Hygiene',
      tip: 'Keep your environment clean. Dispose of rubbish properly to prevent breeding sites for disease-carrying insects and rodents.',
    },
  ],
  dry: [
    {
      icon: Wind,
      color: 'text-orange-600',
      bg: 'bg-orange-50 dark:bg-orange-950/20',
      border: 'border-orange-200 dark:border-orange-800',
      disease: 'Meningitis & Respiratory Infections',
      tip: 'Harmattan dust increases respiratory and meningitis risk. Wear a mask in dusty conditions, keep warm at night, and ensure your meningitis (MenACWY) vaccination is up to date.',
    },
    {
      icon: Thermometer,
      color: 'text-amber-600',
      bg: 'bg-amber-50 dark:bg-amber-950/20',
      border: 'border-amber-200 dark:border-amber-800',
      disease: 'Dehydration & Heat Illness',
      tip: 'Drink at least 2 litres of safe water daily in the dry season. Eat fruits and vegetables, rest in shade during peak heat hours (11am–3pm), and watch for dizziness or confusion.',
    },
    {
      icon: Droplets,
      color: 'text-indigo-600',
      bg: 'bg-indigo-50 dark:bg-indigo-950/20',
      border: 'border-indigo-200 dark:border-indigo-800',
      disease: 'Skin & Eye Infections',
      tip: 'Dry air and dust irritate eyes and skin. Use clean water to wash your face and hands regularly, and avoid touching your eyes with unwashed hands.',
    },
  ],
  general: [
    {
      icon: Shield,
      color: 'text-purple-600',
      bg: 'bg-purple-50 dark:bg-purple-950/20',
      border: 'border-purple-200 dark:border-purple-800',
      disease: 'Vaccination',
      tip: 'Keep your vaccination record up to date. Children should receive scheduled vaccines (polio, measles, hepatitis B). Adults should get annual flu shots and maintain tetanus coverage.',
    },
    {
      icon: Activity,
      color: 'text-teal-600',
      bg: 'bg-teal-50 dark:bg-teal-950/20',
      border: 'border-teal-200 dark:border-teal-800',
      disease: 'Early Screening',
      tip: 'Visit a health centre if symptoms persist more than 48 hours. Early diagnosis and treatment of malaria, typhoid, and TB greatly improve outcomes and reduce community spread.',
    },
  ],
};

const COLORS = [
  'hsl(188 91% 37%)', 'hsl(38 92% 50%)', 'hsl(0 72% 60%)',
  'hsl(142 76% 36%)', 'hsl(221 83% 53%)', 'hsl(280 80% 50%)',
];

// ─── Helpers ─────────────────────────────────────────────────────────────────
const formatWeekLabel = (weekStr) => {
  try {
    const d = new Date(weekStr + 'T00:00:00');
    return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
  } catch {
    return weekStr;
  }
};

const isRainySeason = () => {
  const m = new Date().getMonth(); // 0-based
  return m >= 3 && m <= 9; // April–October
};

// ─── Sub-component: LoadingChart ─────────────────────────────────────────────
const LoadingChart = ({ height = 300 }) => (
  <div className={`flex items-center justify-center`} style={{ height }}>
    <div className="flex flex-col items-center gap-3 text-muted-foreground">
      <Loader2 className="h-8 w-8 animate-spin text-primary/60" />
      <span className="text-sm">Fetching data…</span>
    </div>
  </div>
);

// ─── Sub-component: SampleDataNotice ────────────────────────────────────────
const SampleDataNotice = () => (
  <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/40 border rounded px-3 py-1.5 mt-2">
    <Info className="h-3.5 w-3.5 shrink-0" />
    Showing representative sample data — live data will appear as screenings are recorded.
  </div>
);

// ─── Main component ───────────────────────────────────────────────────────────
const TrendsDashboard = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [sendingAlerts, setSendingAlerts] = useState(false);
  const [diseaseRows, setDiseaseRows] = useState(diseases);
  const [summary, setSummary] = useState({
    total_predictions: 0,
    top_disease: 'No predictions yet',
    active_this_week: 0,
    diseases_tracked: diseases.length,
    region: 'Bamenda',
    total_feedback: 0,
    feedback_accuracy: null,
  });
  const [apiDiseaseData, setApiDiseaseData] = useState([]);
  const [apiTrendRows, setApiTrendRows] = useState([]);
  const [heatmapRows, setHeatmapRows] = useState([]);
  const [usingFallback, setUsingFallback] = useState({
    topDiseases: false, trends: false, heatmap: false,
  });
  const [loading, setLoading] = useState({
    summary: true, topDiseases: true, trends: true, heatmap: true,
  });
  const [showAllTips, setShowAllTips] = useState(false);

  useEffect(() => {
    getAnalyticsSummary()
      .then((res) => setSummary(res.data))
      .catch(() => {})
      .finally(() => setLoading(p => ({ ...p, summary: false })));

    getDiseases()
      .then((res) => { if (Array.isArray(res.data)) setDiseaseRows(res.data); })
      .catch(() => setDiseaseRows(diseases));

    const fallbackTopDiseases = [
      { name: 'Malaria', cases: 850 }, { name: 'Respiratory Infections', cases: 680 },
      { name: 'Typhoid Fever', cases: 540 }, { name: 'Intestinal Parasites', cases: 420 },
      { name: 'Iron Deficiency Anemia', cases: 380 }, { name: 'Hypertension', cases: 350 },
      { name: 'Skin Infections', cases: 290 }, { name: 'Cystitis UTI', cases: 250 },
      { name: 'Cholera', cases: 210 }, { name: 'Diabetes Mellitus', cases: 180 },
    ];
    getTopDiseases()
      .then((res) => {
        const rows = Array.isArray(res.data) ? res.data : [];
        if (rows.length) {
          setApiDiseaseData(rows.map(item => ({
            name: item.name || item.disease,
            cases: item.cases || item.count || 0,
          })));
          setUsingFallback(p => ({ ...p, topDiseases: false }));
        } else {
          setApiDiseaseData(fallbackTopDiseases);
          setUsingFallback(p => ({ ...p, topDiseases: true }));
        }
      })
      .catch(() => {
        setApiDiseaseData(fallbackTopDiseases);
        setUsingFallback(p => ({ ...p, topDiseases: true }));
      })
      .finally(() => setLoading(p => ({ ...p, topDiseases: false })));

    getTrends()
      .then((res) => {
        const rows = Array.isArray(res.data) ? res.data : [];
        setApiTrendRows(rows);
        setUsingFallback(p => ({ ...p, trends: !rows.length }));
      })
      .catch(() => setUsingFallback(p => ({ ...p, trends: true })))
      .finally(() => setLoading(p => ({ ...p, trends: false })));

    getHeatmap()
      .then((res) => {
        const rows = Array.isArray(res.data) ? res.data : [];
        setHeatmapRows(rows);
        setUsingFallback(p => ({ ...p, heatmap: !rows.length }));
      })
      .catch(() => setUsingFallback(p => ({ ...p, heatmap: true })))
      .finally(() => setLoading(p => ({ ...p, heatmap: false })));
  }, []);

  // ── Derived: disease category breakdown from real prediction counts ─────
  const categoryData = useMemo(() => {
    if (!apiDiseaseData.length) return [];
    const nameToCategory = {};
    diseaseRows.forEach(d => {
      if (d.name) nameToCategory[d.name.toLowerCase()] = d.category || 'Other';
    });
    const cats = {};
    apiDiseaseData.forEach(item => {
      const cat = nameToCategory[item.name?.toLowerCase()] || 'Other';
      cats[cat] = (cats[cat] || 0) + (item.cases || 0);
    });
    return Object.entries(cats)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value);
  }, [apiDiseaseData, diseaseRows]);

  // ── Derived: trend chart data (pivoted for Recharts) ─────────────────────
  const trendChartData = useMemo(() => {
    if (!apiTrendRows.length) return SEASONAL_FALLBACK;
    const byWeek = {};
    apiTrendRows.forEach((row) => {
      const label = formatWeekLabel(row.week);
      byWeek[row.week] = byWeek[row.week] || { month: label, _iso: row.week };
      byWeek[row.week][row.disease] = (byWeek[row.week][row.disease] || 0) + row.count;
    });
    return Object.values(byWeek).sort((a, b) => a._iso.localeCompare(b._iso));
  }, [apiTrendRows]);

  const trendLines = useMemo(() => {
    if (!apiTrendRows.length) return ['Malaria', 'Respiratory', 'Typhoid', 'Cholera'];
    return [...new Set(apiTrendRows.map(r => r.disease))].slice(0, 5);
  }, [apiTrendRows]);

  // ── Outbreak alert computation ────────────────────────────────────────────
  const outbreakAlerts = useMemo(() => {
    if (!apiDiseaseData.length) return [];
    const total = summary.total_predictions || apiDiseaseData.reduce((s, d) => s + (d.cases || 0), 0) || 1;
    const rainy = isRainySeason();
    const alerts = [];
    apiDiseaseData.forEach(item => {
      const count = item.cases || 0;
      const pct = Math.round((count / total) * 100);
      let level = null;
      let reason = '';
      if (pct >= 35) { level = 'high'; reason = `${pct}% of all screenings`; }
      else if (pct >= 20) { level = 'medium'; reason = `${pct}% of all screenings`; }
      else if (rainy && (item.name === 'Malaria' || item.name === 'Cholera') && pct >= 10) {
        level = 'watch'; reason = `Rainy-season risk – ${pct}% of screenings`;
      }
      if (level) alerts.push({ disease: item.name, count, pct, level, reason });
    });
    return alerts.sort((a, b) => {
      const rank = { high: 0, medium: 1, watch: 2 };
      return rank[a.level] - rank[b.level];
    }).slice(0, 4);
  }, [apiDiseaseData, summary]);

  // ── Sensitization tips for current season ────────────────────────────────
  const currentTips = useMemo(() => {
    const rainy = isRainySeason();
    return [...(rainy ? SENSITIZATION.rainy : SENSITIZATION.dry), ...SENSITIZATION.general];
  }, []);

  // ── Stat cards ────────────────────────────────────────────────────────────
  const insights = [
    { title: 'Total Screenings', value: summary.total_predictions.toLocaleString(), change: 'Symptom predictions recorded', icon: Users, color: 'text-blue-600', bg: 'from-blue-500/5' },
    { title: 'Top Disease', value: summary.top_disease, change: 'Most frequent prediction', icon: AlertCircle, color: 'text-red-600', bg: 'from-red-500/5' },
    { title: 'Active This Week', value: summary.active_this_week.toLocaleString(), change: 'Predictions in last 7 days', icon: Activity, color: 'text-orange-600', bg: 'from-orange-500/5' },
    { title: 'Coverage', value: `${summary.diseases_tracked} Diseases`, change: `Serving ${summary.region}`, icon: ShieldCheck, color: 'text-green-600', bg: 'from-green-500/5' },
    { title: 'Community Accuracy', value: summary.feedback_accuracy != null ? `${summary.feedback_accuracy}%` : '—', change: summary.total_feedback ? `${summary.total_feedback} user reports` : 'Submit feedback after clinic', icon: ShieldCheck, color: 'text-emerald-600', bg: 'from-emerald-500/5' },
  ];

  const commonInBamenda = diseaseRows.filter(d => d.featured || d.commonInBamenda).slice(0, 6);

  // ─── JSX ─────────────────────────────────────────────────────────────────
  return (
    <>
      <Helmet>
        <title>Health Trends Dashboard - MediGuard Bamenda</title>
        <meta name="description" content="Community health trends, outbreak alerts, and disease prevention sensitization for Bamenda." />
      </Helmet>

      <div className="min-h-screen medical-page py-8 sm:py-12">
        <div className="container mx-auto px-4 max-w-7xl">

          {/* Page heading */}
          <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8 flex flex-col items-center">
            <div className="mb-4">
              <img src="/mediguard.png" alt="MediGuard Logo" className="logo-sm" />
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold mb-3">Community Health Trends</h1>
            <p className="text-base sm:text-lg text-muted-foreground max-w-2xl">
              Real-time insights from MediGuard Bamenda screenings, with outbreak alerts and prevention tips.
            </p>
          </motion.div>

          {/* ── Stat cards ───────────────────────────────────────────────── */}
          <motion.div
            initial="hidden" animate="visible"
            variants={{ visible: { transition: { staggerChildren: 0.07 } } }}
            className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-4 mb-8"
          >
            {insights.map((insight, i) => (
              <motion.div key={i} variants={{ hidden: { opacity: 0, y: 14 }, visible: { opacity: 1, y: 0 } }}>
                <Card className={`medical-panel bg-gradient-to-br ${insight.bg} to-transparent h-full`}>
                  <CardHeader className="flex flex-col sm:flex-row items-center sm:items-center justify-between gap-1 pb-1 sm:pb-2 p-2 sm:p-6">
                    <CardTitle className="text-[10px] sm:text-sm font-medium text-muted-foreground text-center sm:text-left leading-tight">
                      {insight.title}
                    </CardTitle>
                    <insight.icon className={`h-4 w-4 ${insight.color} flex-shrink-0`} />
                  </CardHeader>
                  <CardContent className="p-2 pt-0 sm:p-6 sm:pt-0 text-center sm:text-left">
                    {loading.summary
                      ? <div className="h-7 w-16 bg-muted animate-pulse rounded mx-auto sm:mx-0" />
                      : <div className="text-xs sm:text-2xl font-bold truncate">{insight.value}</div>
                    }
                    <p className="hidden sm:block text-xs text-muted-foreground mt-1">{insight.change}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </motion.div>

          {/* ── Outbreak Alerts ──────────────────────────────────────────── */}
          <AnimatePresence>
            {outbreakAlerts.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mb-8"
              >
                <Card className="border-orange-300 dark:border-orange-700 bg-orange-50/60 dark:bg-orange-950/20">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-3 flex-wrap">
                      <div>
                        <CardTitle className="flex items-center gap-2 text-orange-800 dark:text-orange-300">
                          <Bell className="h-5 w-5" />Outbreak Surveillance Alerts
                        </CardTitle>
                        <CardDescription className="mt-1">
                          Based on current screening patterns — not a confirmed outbreak declaration.
                        </CardDescription>
                      </div>
                      {user && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-orange-400 text-orange-700 hover:bg-orange-100 dark:text-orange-300 shrink-0"
                          disabled={sendingAlerts}
                          onClick={async () => {
                            setSendingAlerts(true);
                            try {
                              const res = await sendOutbreakAlerts();
                              toast({
                                title: 'Alert emails sent',
                                description: res.data.message,
                              });
                            } catch {
                              toast({ variant: 'destructive', title: 'Send failed', description: 'Could not send alert emails. Check SMTP settings.' });
                            } finally {
                              setSendingAlerts(false);
                            }
                          }}
                        >
                          {sendingAlerts
                            ? <><Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />Sending…</>
                            : <><Send className="h-3.5 w-3.5 mr-1.5" />Notify Subscribers</>
                          }
                        </Button>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
                      {outbreakAlerts.map((alert) => {
                        const colors = {
                          high: 'border-red-300 bg-red-50 dark:bg-red-950/30 dark:border-red-700',
                          medium: 'border-orange-300 bg-orange-50 dark:bg-orange-950/30 dark:border-orange-700',
                          watch: 'border-yellow-300 bg-yellow-50 dark:bg-yellow-950/30 dark:border-yellow-700',
                        };
                        const labelColors = {
                          high: 'bg-red-600 text-white',
                          medium: 'bg-orange-500 text-white',
                          watch: 'bg-yellow-500 text-white',
                        };
                        const label = { high: 'HIGH RISK', medium: 'ELEVATED', watch: 'WATCH' };
                        return (
                          <motion.div
                            key={alert.disease}
                            initial={{ scale: 0.94, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            className={`rounded-lg border p-4 ${colors[alert.level]}`}
                          >
                            <div className="flex items-start justify-between gap-2 mb-2">
                              <p className="font-bold text-sm leading-tight">{alert.disease}</p>
                              <Badge className={`text-[10px] ${labelColors[alert.level]} shrink-0`}>
                                {label[alert.level]}
                              </Badge>
                            </div>
                            <p className="text-2xl font-bold">{alert.count.toLocaleString()}</p>
                            <p className="text-xs text-muted-foreground">{alert.reason}</p>
                          </motion.div>
                        );
                      })}
                    </div>
                    <p className="text-xs text-muted-foreground mt-4 flex items-center gap-1.5">
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                      Alert thresholds: High ≥35% of all screenings, Elevated ≥20%, Watch = rainy-season sensitive disease ≥10%.
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>

          {/* ── Main charts grid ─────────────────────────────────────────── */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-8">

            {/* Top 10 diseases bar */}
            <Card className="medical-panel">
              <CardHeader>
                <CardTitle>Top 10 Screened Conditions</CardTitle>
                <CardDescription>Aggregate top predictions from the backend database</CardDescription>
              </CardHeader>
              <CardContent>
                {loading.topDiseases ? <LoadingChart /> : (
                  <>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={apiDiseaseData.slice(0, 10)} layout="vertical" margin={{ left: 8, right: 16 }}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" tick={{ fontSize: 11 }} />
                        <YAxis dataKey="name" type="category" width={110} tick={{ fontSize: 11 }} />
                        <Tooltip formatter={(v) => [v.toLocaleString(), 'Screenings']} />
                        <Bar dataKey="cases" fill="hsl(188 91% 37%)" radius={[0, 4, 4, 0]}>
                          {apiDiseaseData.map((_, i) => (
                            <Cell key={i} fill={COLORS[i % COLORS.length]} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                    {usingFallback.topDiseases && <SampleDataNotice />}
                  </>
                )}
              </CardContent>
            </Card>

            {/* Category pie chart — prediction-weighted */}
            <Card className="medical-panel">
              <CardHeader>
                <CardTitle>Disease Categories</CardTitle>
                <CardDescription>Prediction count weighted by disease category</CardDescription>
              </CardHeader>
              <CardContent>
                {loading.topDiseases ? <LoadingChart /> : (
                  <>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={categoryData}
                          cx="50%"
                          cy="50%"
                          outerRadius={100}
                          dataKey="value"
                          labelLine={false}
                          label={({ name, percent }) =>
                            percent > 0.05 ? `${name}: ${(percent * 100).toFixed(0)}%` : ''
                          }
                        >
                          {categoryData.map((_entry, i) => (
                            <Cell key={i} fill={COLORS[i % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(v) => [v.toLocaleString(), 'Screenings']} />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                    {usingFallback.topDiseases && <SampleDataNotice />}
                  </>
                )}
              </CardContent>
            </Card>

            {/* Seasonal trends line chart */}
            <Card className="lg:col-span-2 medical-panel">
              <CardHeader>
                <CardTitle>Seasonal Disease Trends</CardTitle>
                <CardDescription>
                  {apiTrendRows.length
                    ? `Live data — ${trendChartData.length} weekly data points from the database`
                    : 'Documented seasonal patterns for Bamenda (sample data until screenings accumulate)'
                  }
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading.trends ? <LoadingChart /> : (
                  <>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={trendChartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="month"
                          tick={{ fontSize: 11 }}
                          interval="preserveStartEnd"
                        />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip />
                        <Legend />
                        {trendLines.map((disease, i) => (
                          <Line
                            key={disease}
                            type="monotone"
                            dataKey={disease}
                            name={disease}
                            stroke={COLORS[i % COLORS.length]}
                            strokeWidth={2}
                            dot={apiTrendRows.length < 30}
                            activeDot={{ r: 5 }}
                          />
                        ))}
                      </LineChart>
                    </ResponsiveContainer>
                    {usingFallback.trends && <SampleDataNotice />}
                  </>
                )}
              </CardContent>
            </Card>
          </div>

          {/* ── Second row: age distribution + endemic highlights ─────────── */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 mb-8">
            <Card className="lg:col-span-2 medical-panel">
              <CardHeader>
                <CardTitle>Age Group Distribution</CardTitle>
                <CardDescription>
                  Illustrative distribution across age groups (representative data — full breakdown available when age is collected during screening)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={AGE_GROUP_DATA}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="age" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip formatter={(v) => [v.toLocaleString(), 'Cases']} />
                    <Bar dataKey="cases" fill="hsl(38 92% 50%)" radius={[4, 4, 0, 0]}>
                      {AGE_GROUP_DATA.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} opacity={0.85} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="medical-panel">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-orange-500" />Endemic Highlights
                </CardTitle>
                <CardDescription>Highly prevalent in Bamenda region</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {commonInBamenda.map((disease) => (
                    <div key={disease.id} className="flex justify-between items-center border-b pb-2 last:border-0">
                      <div>
                        <p className="font-semibold text-sm">{disease.name}</p>
                        <p className="text-xs text-muted-foreground">{disease.category}</p>
                      </div>
                      <Badge variant={disease.severity === 'High' ? 'destructive' : 'secondary'} className="text-[10px]">
                        {disease.severity}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* ── Heatmap ─────────────────────────────────────────────────── */}
          {!loading.heatmap && heatmapRows.length > 0 && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
              <Card className="medical-panel">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MapPinned className="h-5 w-5 text-primary" />Regional Heatmap
                  </CardTitle>
                  <CardDescription>Prediction activity by region and disease</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                    {heatmapRows.map((row) => (
                      <div key={`${row.region}-${row.disease}`} className="rounded-lg border bg-background p-4">
                        <p className="font-semibold text-sm">{row.region}</p>
                        <p className="text-xs text-muted-foreground">{row.disease}</p>
                        <p className="text-2xl font-bold text-primary mt-1">{row.count.toLocaleString()}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* ── Prevention Sensitization ──────────────────────────────────── */}
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
            <Card className="medical-panel border-green-200 dark:border-green-800">
              <CardHeader>
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div>
                    <CardTitle className="flex items-center gap-2 text-green-800 dark:text-green-300">
                      <Shield className="h-5 w-5" />
                      Disease Prevention Sensitization
                      <Badge variant="outline" className="text-xs border-green-300 text-green-700 dark:text-green-400">
                        {isRainySeason() ? 'Rainy Season' : 'Dry Season'}
                      </Badge>
                    </CardTitle>
                    <CardDescription className="mt-1">
                      Seasonal health tips for the Bamenda community — share these with family and neighbours
                    </CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs"
                    onClick={() => setShowAllTips(v => !v)}
                  >
                    {showAllTips ? <><ChevronUp className="h-3.5 w-3.5 mr-1" />Show Less</> : <><ChevronDown className="h-3.5 w-3.5 mr-1" />Show All Tips</>}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  <AnimatePresence>
                    {(showAllTips ? currentTips : currentTips.slice(0, 3)).map((tip, i) => (
                      <motion.div
                        key={tip.disease}
                        initial={{ opacity: 0, scale: 0.96 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.96 }}
                        transition={{ delay: i * 0.05 }}
                        className={`rounded-xl border p-4 ${tip.bg} ${tip.border}`}
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <div className={`p-1.5 rounded-lg bg-white/60 dark:bg-black/20`}>
                            <tip.icon className={`h-4 w-4 ${tip.color}`} />
                          </div>
                          <h4 className={`font-bold text-sm ${tip.color}`}>{tip.disease}</h4>
                        </div>
                        <p className="text-sm text-foreground/85 leading-relaxed">{tip.tip}</p>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>

                {/* Monthly context banner */}
                <div className="mt-5 p-4 rounded-lg bg-primary/5 border border-primary/20 flex items-start gap-3">
                  <Thermometer className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-sm text-foreground mb-1">
                      {isRainySeason() ? 'Rainy Season Advisory (April – October)' : 'Dry Season Advisory (November – March)'}
                    </p>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {isRainySeason()
                        ? 'The rainy season in Bamenda brings increased risk of malaria, cholera, and typhoid. Communities near rivers and low-lying areas should take extra precautions. Report unusual clusters of fever and diarrhoea to the nearest health centre immediately.'
                        : 'The dry harmattan season increases respiratory illnesses and meningitis risk. Dust levels rise significantly — cover water containers, use nose masks in very dusty conditions, and ensure children are vaccinated against meningococcal disease.'
                      }
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* ── Data source notes ────────────────────────────────────────── */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 mt-8">
            {[
              { icon: Database, title: 'Top Diseases', text: 'Counts come from saved symptom predictions. Each screening contributes the model\'s top match to the aggregate.' },
              { icon: TrendingUp, title: 'Seasonal Trends', text: 'The backend groups predictions by ISO week. If no live records exist, the page shows documented seasonal sample patterns for Bamenda.' },
              { icon: MapPinned, title: 'Heatmap', text: 'Regional rows show prediction activity by area. Outbreak alerts are computed automatically from prediction frequency thresholds.' },
            ].map((note) => (
              <Card key={note.title} className="medical-panel">
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <note.icon className="h-5 w-5 text-primary" />{note.title}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground leading-relaxed">{note.text}</p>
                </CardContent>
              </Card>
            ))}
          </div>

        </div>
      </div>
    </>
  );
};

export default TrendsDashboard;
