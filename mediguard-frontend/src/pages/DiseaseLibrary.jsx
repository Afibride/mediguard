
import React, { useEffect, useState } from 'react';
import { Helmet } from 'react-helmet';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Search, TrendingUp, AlertTriangle, BookOpen, Database, ShieldCheck } from 'lucide-react';
import { diseases } from '@/data/diseases';
import { getDiseases } from '@/services/api';
import { getCommonName } from '@/data/layman';
import SeasonalBanner from '@/components/SeasonalBanner';

const DiseaseLibrary = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [severityFilter, setSeverityFilter] = useState('All');
  const [commonOnly, setCommonOnly] = useState(false);
  const [diseaseRows, setDiseaseRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dataSource, setDataSource] = useState('Backend system');

  useEffect(() => {
    setLoading(true);
    getDiseases()
      .then((res) => {
        if (Array.isArray(res.data) && res.data.length) {
          setDiseaseRows(res.data.map((d) => ({
            ...d,
            id: d.id || d.slug,
            commonInBamenda: d.commonInBamenda ?? d.featured,
            symptoms: d.symptoms || [],
          })));
          setDataSource('Backend system database');
        }
      })
      .catch(() => {
        setDiseaseRows(diseases);
        setDataSource('Backend unavailable - emergency local fallback');
      })
      .finally(() => setLoading(false));
  }, []);

  const categories = ['All', ...new Set(diseaseRows.map(d => d.category))];
  const severities = ['All', 'Low', 'Medium', 'High'];

  const filteredDiseases = diseaseRows.filter((disease) => {
    const q = searchQuery.toLowerCase();
    const commonName = (getCommonName(disease.name) || '').toLowerCase();
    const matchesSearch = disease.name.toLowerCase().includes(q) ||
                          commonName.includes(q) ||
                          (disease.description || '').toLowerCase().includes(q) ||
                          (disease.symptoms || []).some(s => s.toLowerCase().includes(q));
    const matchesCategory = categoryFilter === 'All' || disease.category === categoryFilter;
    const matchesSeverity = severityFilter === 'All' || disease.severity === severityFilter;
    const matchesCommon = !commonOnly || disease.commonInBamenda;

    return matchesSearch && matchesCategory && matchesSeverity && matchesCommon;
  });

  const getSeverityBadge = (severity) => {
    switch (severity.toLowerCase()) {
      case 'high':
      case 'critical':
        return 'destructive';
      case 'medium':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  return (
    <>
      <Helmet>
        <title>Disease Library — MediGuard Bamenda | Symptoms, Causes & Treatment</title>
        <meta name="description" content="Browse MediGuard's comprehensive disease library. Learn about symptoms, causes, treatment, and prevention for 30+ conditions common in Bamenda, Cameroon." />
        <meta name="keywords" content="disease library, Bamenda diseases, malaria symptoms, typhoid treatment, cholera prevention, disease information, health library Cameroon" />
        <link rel="canonical" href="https://mediguard.info/disease-library" />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://mediguard.info/disease-library" />
        <meta property="og:title" content="Disease Library — MediGuard Bamenda" />
        <meta property="og:description" content="Comprehensive library of 30+ diseases common in Bamenda. Learn about symptoms, causes, treatment, and prevention." />
        <meta property="og:image" content="https://mediguard.info/mediguard.png" />
        <meta property="og:site_name" content="MediGuard" />
        <meta name="twitter:card" content="summary" />
        <meta name="twitter:title" content="Disease Library — MediGuard Bamenda" />
        <meta name="twitter:description" content="30+ diseases covered. Learn symptoms, causes, and treatment for Bamenda community health." />
        <meta name="twitter:image" content="https://mediguard.info/mediguard.png" />
      </Helmet>

      <div className="min-h-screen medical-page py-8 sm:py-12">
        <div className="container mx-auto px-4 max-w-7xl">
          <SeasonalBanner compact className="mb-5" />
          <div className="text-center mb-8 flex flex-col items-center">
            <div className="mb-4">
              <img 
                src="/mediguard.png" 
                alt="MediGuard Logo" 
                className="logo-sm"
              />
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold mb-4">Disease Library</h1>
            <p className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto">
              Explore symptoms, causes, prevention, and treatment summaries from the MediGuard knowledge base.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-2 sm:gap-4 mb-6">
            {[
              { label: 'Diseases Loaded', value: diseaseRows.length, icon: BookOpen },
              { label: 'Categories', value: categories.length - 1, icon: Database },
              { label: 'Common in Bamenda', value: diseaseRows.filter((d) => d.commonInBamenda || d.featured).length, icon: ShieldCheck },
            ].map((item) => (
              <Card key={item.label} className="medical-panel">
                <CardContent className="p-2.5 sm:p-5 flex flex-col sm:flex-row items-center text-center sm:text-left gap-2 sm:gap-4 min-h-[108px] sm:min-h-0">
                  <div className="h-8 w-8 sm:h-10 sm:w-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center flex-shrink-0">
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

          <Card className="mb-8 medical-panel">
            <CardContent className="pt-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
                <div className="relative col-span-2 md:col-span-2">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                  <Input
                    type="text"
                    placeholder="Search by name, symptom, or description..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 bg-background text-base"
                  />
                </div>
                
                <div className="min-w-0">
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-2 sm:px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={categoryFilter}
                    onChange={(e) => setCategoryFilter(e.target.value)}
                  >
                    {categories.map(c => <option key={c} value={c}>Category: {c}</option>)}
                  </select>
                </div>

                <div className="min-w-0">
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-2 sm:px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={severityFilter}
                    onChange={(e) => setSeverityFilter(e.target.value)}
                  >
                    {severities.map(s => <option key={s} value={s}>Severity: {s}</option>)}
                  </select>
                </div>

                <div className="col-span-2 md:col-span-4 flex flex-col sm:flex-row sm:items-center gap-3 sm:justify-between">
                  <div className="flex items-center space-x-2">
                  <Checkbox
                    id="common-filter"
                    checked={commonOnly}
                    onCheckedChange={(checked) => setCommonOnly(checked)}
                  />
                  <Label htmlFor="common-filter" className="text-sm font-medium cursor-pointer">
                    Show only diseases common in Bamenda
                  </Label>
                  </div>
                  <span className="text-xs text-muted-foreground">Data source: {dataSource}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {loading && (
            <div className="py-12 text-center text-muted-foreground">
              Loading disease data from MediGuard backend...
            </div>
          )}

          {!loading && (
          <div className="grid grid-flow-col grid-rows-3 auto-cols-[minmax(250px,84vw)] gap-3 overflow-x-auto pb-3 md:grid-flow-row md:grid-rows-none md:auto-cols-auto md:grid-cols-2 md:overflow-visible md:pb-0 lg:grid-cols-3 lg:gap-6">
            {filteredDiseases.map((disease) => (
              <Link key={disease.id} to={`/disease/${disease.id}`}>
                <Card className="h-full hover:shadow-xl transition-all duration-300 cursor-pointer medical-panel hover:border-primary/50 flex flex-col">
                  <CardHeader className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <div className="px-3 py-1 rounded-full text-sm font-semibold bg-primary/10 text-primary inline-block">
                          {disease.name}
                        </div>
                        {getCommonName(disease.name) && (
                          <p className="text-xs text-muted-foreground mt-1 pl-1">
                            {getCommonName(disease.name)}
                          </p>
                        )}
                      </div>
                      {disease.severity.toLowerCase() === 'high' && (
                        <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0 ml-2" />
                      )}
                    </div>
                    <CardDescription className="text-foreground/80">
                      {disease.description || 'No description available from the backend yet.'}
                    </CardDescription>
                    <div className="flex flex-wrap gap-1.5 pt-2">
                      {(disease.symptoms || []).slice(0, 4).map((symptom) => (
                        <Badge key={symptom} variant="outline" className="text-[11px] bg-muted/50">
                          {symptom}
                        </Badge>
                      ))}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between border-t pt-3">
                        <span className="text-sm text-muted-foreground">Category:</span>
                        <span className="text-sm font-semibold">{disease.category}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Severity:</span>
                        <Badge variant={getSeverityBadge(disease.severity)} className="text-xs">
                          {disease.severity}
                        </Badge>
                      </div>
                      {disease.commonInBamenda && (
                        <div className="flex items-center gap-1 text-orange-600">
                          <TrendingUp className="h-4 w-4" />
                          <span className="text-xs font-semibold">Common in Bamenda</span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
          )}

          {!loading && filteredDiseases.length === 0 && (
            <div className="text-center py-12">
              <p className="text-muted-foreground text-lg">No diseases found matching your filters.</p>
              <Button 
                variant="link" 
                onClick={() => {
                  setSearchQuery('');
                  setCategoryFilter('All');
                  setSeverityFilter('All');
                  setCommonOnly(false);
                }}
              >
                Clear Filters
              </Button>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default DiseaseLibrary;
