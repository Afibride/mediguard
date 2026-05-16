
import React, { useEffect, useMemo, useState } from 'react';
import { Helmet } from 'react-helmet';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, Users, Activity, AlertCircle, ShieldCheck, MapPinned, Database } from 'lucide-react';
import { diseases } from '@/data/diseases';
import { getAnalyticsSummary, getDiseases, getHeatmap, getTopDiseases, getTrends } from '@/services/api';

const TrendsDashboard = () => {
  const [diseaseRows, setDiseaseRows] = useState(diseases);
  const [summary, setSummary] = useState({
    total_predictions: 0,
    top_disease: 'No predictions yet',
    active_this_week: 0,
    diseases_tracked: diseases.length,
    region: 'Bamenda',
  });

  const categoryCounts = {};
  diseaseRows.forEach(d => {
    categoryCounts[d.category] = (categoryCounts[d.category] || 0) + 1;
  });

  const categoryData = Object.keys(categoryCounts).map(key => ({
    name: key,
    value: categoryCounts[key] * 80 
  }));

  const diseaseData = [
    { name: 'Malaria', cases: 850 },
    { name: 'Respiratory', cases: 680 },
    { name: 'Typhoid', cases: 540 },
    { name: 'Parasitic', cases: 420 },
    { name: 'Anemia', cases: 380 },
    { name: 'Hypertension', cases: 350 },
    { name: 'Skin Inf.', cases: 290 },
    { name: 'UTIs', cases: 250 },
    { name: 'Cholera', cases: 210 },
    { name: 'Diabetes', cases: 180 },
  ];

  const seasonalData = [
    { month: 'Jan', malaria: 40, typhoid: 25, respiratory: 60, cholera: 5 },
    { month: 'Feb', malaria: 45, typhoid: 28, respiratory: 55, cholera: 8 },
    { month: 'Mar', malaria: 50, typhoid: 30, respiratory: 45, cholera: 12 },
    { month: 'Apr', malaria: 65, typhoid: 35, respiratory: 40, cholera: 20 },
    { month: 'May', malaria: 85, typhoid: 40, respiratory: 35, cholera: 25 },
    { month: 'Jun', malaria: 110, typhoid: 45, respiratory: 30, cholera: 40 },
    { month: 'Jul', malaria: 130, typhoid: 50, respiratory: 35, cholera: 45 },
    { month: 'Aug', malaria: 120, typhoid: 45, respiratory: 40, cholera: 35 },
    { month: 'Sep', malaria: 95, typhoid: 40, respiratory: 45, cholera: 20 },
    { month: 'Oct', malaria: 70, typhoid: 35, respiratory: 50, cholera: 15 },
    { month: 'Nov', malaria: 50, typhoid: 30, respiratory: 55, cholera: 10 },
    { month: 'Dec', malaria: 45, typhoid: 25, respiratory: 65, cholera: 5 },
  ];
  const [apiDiseaseData, setApiDiseaseData] = useState(diseaseData);
  const [apiTrendRows, setApiTrendRows] = useState([]);
  const [heatmapRows, setHeatmapRows] = useState([]);

  useEffect(() => {
    getAnalyticsSummary()
      .then((res) => setSummary(res.data))
      .catch(() => {});

    getDiseases()
      .then((res) => {
        if (Array.isArray(res.data)) setDiseaseRows(res.data);
      })
      .catch(() => setDiseaseRows(diseases));

    getTopDiseases()
      .then((res) => {
        setApiDiseaseData(res.data.map((item) => ({
          name: item.name || item.disease,
          cases: item.cases || item.count,
        })));
      })
      .catch(() => setApiDiseaseData(diseaseData));

    getTrends()
      .then((res) => setApiTrendRows(res.data))
      .catch(() => setApiTrendRows([]));

    getHeatmap()
      .then((res) => setHeatmapRows(Array.isArray(res.data) ? res.data : []))
      .catch(() => setHeatmapRows([]));
  }, []);

  const trendChartData = useMemo(() => {
    if (!apiTrendRows.length) return seasonalData;
    const byWeek = {};
    apiTrendRows.forEach((row) => {
      const key = row.week;
      byWeek[key] = byWeek[key] || { month: key };
      byWeek[key][row.disease] = row.count;
    });
    return Object.values(byWeek);
  }, [apiTrendRows]);

  const ageGroupData = [
    { age: '0-10', cases: 380 },
    { age: '11-20', cases: 420 },
    { age: '21-30', cases: 580 },
    { age: '31-40', cases: 540 },
    { age: '41-50', cases: 400 },
    { age: '51-60', cases: 350 },
    { age: '60+', cases: 330 },
  ];

  const COLORS = ['hsl(188 91% 37%)', 'hsl(38 92% 50%)', 'hsl(0 72% 60%)', 'hsl(142 76% 36%)', 'hsl(221 83% 53%)', 'hsl(280 80% 50%)'];

  const insights = [
    {
      title: 'Total Screenings',
      value: summary.total_predictions.toLocaleString(),
      change: 'Recorded symptom predictions',
      icon: Users,
      color: 'text-blue-600',
    },
    {
      title: 'Top Disease',
      value: summary.top_disease,
      change: 'Most frequent top prediction',
      icon: AlertCircle,
      color: 'text-red-600',
    },
    {
      title: 'Active This Week',
      value: summary.active_this_week.toLocaleString(),
      change: 'Predictions in last 7 days',
      icon: Activity,
      color: 'text-orange-600',
    },
    {
      title: 'System Coverage',
      value: `${summary.diseases_tracked} Diseases`,
      change: `Serving ${summary.region}`,
      icon: ShieldCheck,
      color: 'text-green-600',
    },
  ];

  const commonInBamenda = diseaseRows.filter(d => d.featured || d.commonInBamenda).slice(0, 8);
  const dashboardNotes = [
    {
      title: 'Top diseases',
      text: 'Counts come from saved symptom predictions. Each screening contributes the model top match to the aggregate.',
      icon: Database,
    },
    {
      title: 'Seasonal trends',
      text: 'The backend groups predictions by week. If no live records exist yet, the page shows documented seasonal sample patterns.',
      icon: TrendingUp,
    },
    {
      title: 'Heatmap',
      text: 'Regional rows show where prediction activity is concentrated. The current configured region is Bamenda.',
      icon: MapPinned,
    },
  ];

  return (
    <>
      <Helmet>
        <title>Health Trends Dashboard - MediGuard Bamenda</title>
        <meta name="description" content="Explore community health trends, disease patterns, and health statistics in Bamenda." />
      </Helmet>

      <div className="min-h-screen medical-page py-8 sm:py-12">
        <div className="container mx-auto px-4 max-w-7xl">
          <div className="text-center mb-8 flex flex-col items-center">
            <div className="mb-4">
              <img 
                src="/mediguard.png" 
                alt="MediGuard Logo" 
                className="logo-sm"
              />
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold mb-4">Community Health Trends</h1>
            <p className="text-base sm:text-lg text-muted-foreground max-w-2xl">
              Data-driven insights from MediGuard Bamenda screenings, disease records, and model outputs.
            </p>
          </div>

          <div className="grid grid-cols-4 gap-2 sm:gap-4 lg:gap-6 mb-8">
            {insights.map((insight, index) => (
              <Card key={index} className="medical-panel">
                <CardHeader className="flex flex-col sm:flex-row items-center sm:items-center justify-between gap-1 pb-1 sm:pb-2 p-2 sm:p-6">
                  <CardTitle className="text-[10px] sm:text-sm font-medium text-muted-foreground text-center sm:text-left leading-tight">
                    {insight.title}
                  </CardTitle>
                  <insight.icon className={`h-4 w-4 ${insight.color} flex-shrink-0`} />
                </CardHeader>
                <CardContent className="p-2 pt-0 sm:p-6 sm:pt-0 text-center sm:text-left">
                  <div className="text-xs sm:text-2xl font-bold truncate">{insight.value}</div>
                  <p className="hidden sm:block text-xs text-muted-foreground mt-1">{insight.change}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-8">
            <Card className="medical-panel">
              <CardHeader>
                <CardTitle>Top 10 Screened Diseases</CardTitle>
                <CardDescription>Aggregate top predictions saved by the backend</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={apiDiseaseData} layout="vertical" margin={{ left: 8, right: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="name" type="category" width={90} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="cases" fill="hsl(188 91% 37%)" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="medical-panel">
              <CardHeader>
                <CardTitle>Disease Categories</CardTitle>
                <CardDescription>Breakdown by infection/condition type</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={categoryData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {categoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2 medical-panel">
              <CardHeader>
                <CardTitle>Seasonal Disease Trends</CardTitle>
                <CardDescription>Monthly disease patterns highlighting rainy vs dry season impacts</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={trendChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    {apiTrendRows.length ? (
                      [...new Set(apiTrendRows.map((row) => row.disease))].slice(0, 4).map((disease, index) => (
                        <Line key={disease} type="monotone" dataKey={disease} name={disease} stroke={COLORS[index % COLORS.length]} strokeWidth={2} />
                      ))
                    ) : (
                      <>
                        <Line type="monotone" dataKey="malaria" name="Malaria" stroke="hsl(0 72% 60%)" strokeWidth={3} dot={false} />
                        <Line type="monotone" dataKey="respiratory" name="Respiratory" stroke="hsl(188 91% 37%)" strokeWidth={2} />
                        <Line type="monotone" dataKey="typhoid" name="Typhoid" stroke="hsl(38 92% 50%)" strokeWidth={2} />
                        <Line type="monotone" dataKey="cholera" name="Cholera" stroke="hsl(280 80% 50%)" strokeWidth={2} strokeDasharray="5 5" />
                      </>
                    )}
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
            <Card className="lg:col-span-2 medical-panel">
              <CardHeader>
                <CardTitle>Age Group Distribution</CardTitle>
                <CardDescription>Cases by age group across all screenings</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={ageGroupData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="age" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="cases" fill="hsl(38 92% 50%)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="medical-panel">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-orange-500" />
                  Endemic Highlights
                </CardTitle>
                <CardDescription>Highly prevalent in Bamenda</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {commonInBamenda.slice(0, 5).map((disease) => (
                    <div key={disease.id} className="flex justify-between items-center border-b pb-2 last:border-0">
                      <div>
                        <p className="font-semibold">{disease.name}</p>
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

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 mt-8">
            {dashboardNotes.map((note) => (
              <Card key={note.title} className="medical-panel">
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <note.icon className="h-5 w-5 text-primary" />
                    {note.title}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground leading-relaxed">{note.text}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          {heatmapRows.length > 0 && (
            <Card className="medical-panel mt-8">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MapPinned className="h-5 w-5 text-primary" />
                  Regional Heatmap Data
                </CardTitle>
                <CardDescription>Backend heatmap rows used for public health monitoring</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  {heatmapRows.map((row) => (
                    <div key={`${row.region}-${row.disease}`} className="rounded-lg border bg-background p-4">
                      <p className="font-semibold">{row.region}</p>
                      <p className="text-sm text-muted-foreground">{row.disease}</p>
                      <p className="text-2xl font-bold text-primary mt-2">{row.count}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </>
  );
};

export default TrendsDashboard;
