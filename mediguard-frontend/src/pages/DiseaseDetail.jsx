
import React, { useEffect, useMemo, useState } from 'react';
import { Helmet } from 'react-helmet';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, AlertCircle, Shield, Activity, Stethoscope, TrendingUp, HelpCircle, BookOpen, Pill, ClipboardList } from 'lucide-react';
import { diseases } from '@/data/diseases';
import { getDiseaseDetail, getDiseases } from '@/services/api';

const DiseaseDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [disease, setDisease] = useState(null);
  const [allDiseases, setAllDiseases] = useState(diseases);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getDiseaseDetail(id),
      getDiseases(),
    ])
      .then(([detailRes, listRes]) => {
        setDisease(detailRes.data);
        if (Array.isArray(listRes.data)) {
          setAllDiseases(listRes.data);
        }
      })
      .catch(() => {
        setDisease(diseases.find(d => d.id === id || d.slug === id));
        setAllDiseases(diseases);
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-muted/30 py-12 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!disease) {
    return (
      <div className="min-h-screen bg-muted/30 py-12">
        <div className="container mx-auto px-4 max-w-4xl text-center">
          <h1 className="text-3xl font-bold mb-4">Disease Not Found</h1>
          <Button onClick={() => navigate('/disease-library')}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Disease Library
          </Button>
        </div>
      </div>
    );
  }

  const relatedDiseases = allDiseases
    .filter(d => d.category === disease.category && (d.id || d.slug) !== (disease.id || disease.slug))
    .slice(0, 3);

  const isHighSeverity = disease.severity?.toLowerCase() === 'high' || disease.severity?.toLowerCase() === 'critical';
  const prevention = Array.isArray(disease.prevention) ? disease.prevention.filter(Boolean) : [disease.prevention].filter(Boolean);
  const extraSections = Object.entries(disease.sections || {})
    .filter(([title, value]) => value && !['Overview', 'Description', 'Definition', 'Treatment', 'Prevention', 'Causes', 'Causes and symptoms'].includes(title))
    .slice(0, 4);

  return (
    <>
      <Helmet>
        <title>{disease.name} - MediGuard Bamenda</title>
        <meta name="description" content={disease.description} />
      </Helmet>

      <div className="min-h-screen medical-page py-8 sm:py-12">
        <div className="container mx-auto px-4 max-w-4xl">
          <div className="mb-6 flex justify-between items-center gap-4">
            <Button variant="outline" onClick={() => navigate('/disease-library')}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              <span className="hidden sm:inline">Back to Library</span>
              <span className="sm:hidden">Back</span>
            </Button>
            <div>
              <img 
                src="/mediguard.png" 
                alt="MediGuard Logo" 
                className="logo-sm"
              />
            </div>
          </div>

          <div className="mb-6">
            <h1 className="text-3xl sm:text-4xl font-bold mb-4 text-balance">{disease.name}</h1>
            <div className="flex flex-wrap gap-3">
              <Badge variant="secondary" className="text-sm">
                Category: {disease.category}
              </Badge>
              <Badge
                variant={isHighSeverity ? 'destructive' : 'secondary'}
                className="text-sm"
              >
                Severity: {disease.severity}
              </Badge>
              {disease.commonInBamenda && (
                <Badge className="bg-orange-500 hover:bg-orange-600 text-white text-sm flex items-center gap-1">
                  <TrendingUp className="h-3 w-3" />
                  Common in Bamenda
                </Badge>
              )}
            </div>
          </div>

          <Card className="mb-6 medical-panel">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-primary" />
                Overview
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-foreground/90 leading-relaxed">{disease.description}</p>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <Card className="medical-panel">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Stethoscope className="h-5 w-5 text-primary" />
                  Common Symptoms
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {disease.symptoms.map((symptom, index) => (
                    <Badge key={index} variant="outline" className="bg-primary/5 text-sm">
                      {symptom}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="medical-panel">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <HelpCircle className="h-5 w-5 text-primary" />
                  Causes & Risks
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-semibold text-sm text-muted-foreground mb-1">Causes</h4>
                  <p className="text-foreground/90">{disease.causes}</p>
                </div>
                <div>
                  <h4 className="font-semibold text-sm text-muted-foreground mb-1">Risk Factors</h4>
                  <p className="text-foreground/90">{disease.riskFactors || 'Risk varies by exposure, immunity, age, environment, and existing health conditions.'}</p>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="mb-6 border-primary medical-panel">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-primary" />
                Prevention Strategies
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {prevention.map((strategy, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <Shield className="h-4 w-4 text-primary mt-1 flex-shrink-0" />
                    <span className="text-foreground/90">{strategy}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card className="mb-8 medical-panel">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Pill className="h-5 w-5 text-primary" />
                Treatment Overview
              </CardTitle>
              <CardDescription>General treatment approach (not medical advice)</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-foreground/90 leading-relaxed">{disease.treatment || 'Treatment depends on diagnosis, severity, and clinical evaluation by a qualified healthcare professional.'}</p>
            </CardContent>
          </Card>

          {extraSections.length > 0 && (
            <div className="mb-8">
              <h3 className="text-2xl font-bold mb-4 flex items-center gap-2">
                <ClipboardList className="h-5 w-5 text-primary" />
                More Encyclopedia Details
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {extraSections.map(([title, value]) => (
                  <Card key={title} className="medical-panel">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg">{title}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground leading-relaxed line-clamp-6">{String(value)}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
          
          {isHighSeverity && (
            <Card className="mb-8 border-destructive bg-destructive/5">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-destructive">
                  <AlertCircle className="h-5 w-5" />
                  Medical Attention
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-foreground/90">
                  Because {disease.name} is a high-severity condition, it is highly recommended to seek professional medical diagnosis and care promptly if you suspect you are infected.
                </p>
              </CardContent>
            </Card>
          )}

          {relatedDiseases.length > 0 && (
            <div className="mb-8">
              <h3 className="text-2xl font-bold mb-4">Related Diseases</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {relatedDiseases.map(rd => (
                  <Link key={rd.id || rd.slug} to={`/disease/${rd.slug || rd.id}`}>
                    <Card className="hover:border-primary/50 transition-colors h-full">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-lg">{rd.name}</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-muted-foreground line-clamp-2">{rd.description}</p>
                      </CardContent>
                    </Card>
                  </Link>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-wrap gap-4 justify-center">
            <Link to="/symptom-checker" className="w-full sm:w-auto">
              <Button size="lg" className="w-full sm:w-auto">
                <Activity className="mr-2 h-5 w-5" />
                Check Your Symptoms
              </Button>
            </Link>
            <Link to="/chat-ai" className="w-full sm:w-auto">
              <Button size="lg" variant="outline" className="w-full sm:w-auto">
                Ask AI Assistant
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </>
  );
};

export default DiseaseDetail;
