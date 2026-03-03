
import React from 'react';
import { Helmet } from 'react-helmet';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, AlertCircle, Shield, Activity, Stethoscope, TrendingUp, HelpCircle } from 'lucide-react';
import { diseases } from '@/data/diseases';

const DiseaseDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const disease = diseases.find(d => d.id === id);

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

  const relatedDiseases = diseases
    .filter(d => d.category === disease.category && d.id !== disease.id)
    .slice(0, 3);

  const isHighSeverity = disease.severity.toLowerCase() === 'high' || disease.severity.toLowerCase() === 'critical';

  return (
    <>
      <Helmet>
        <title>{disease.name} - MediGuard Bamenda</title>
        <meta name="description" content={disease.description} />
      </Helmet>

      <div className="min-h-screen bg-muted/30 py-12">
        <div className="container mx-auto px-4 max-w-4xl">
          <div className="mb-6 flex justify-between items-center">
            <Button variant="outline" onClick={() => navigate('/disease-library')}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Library
            </Button>
            <div>
              <img 
                src="/public/mediguard.png" 
                alt="MediGuard Logo" 
                className="logo-sm"
              />
            </div>
          </div>

          <div className="mb-6">
            <h1 className="text-4xl font-bold mb-4">{disease.name}</h1>
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

          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-primary" />
                Overview
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-foreground/90">{disease.description}</p>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <Card>
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

            <Card>
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
                  <p className="text-foreground/90">{disease.riskFactors}</p>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="mb-6 border-primary">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-primary" />
                Prevention Strategies
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {disease.prevention.map((strategy, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="text-primary mt-1">✓</span>
                    <span className="text-foreground/90">{strategy}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Treatment Overview</CardTitle>
              <CardDescription>General treatment approach (not medical advice)</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-foreground/90">{disease.treatment}</p>
            </CardContent>
          </Card>
          
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
                  <Link key={rd.id} to={`/disease/${rd.id}`}>
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
            <Link to="/symptom-checker">
              <Button size="lg">
                <Activity className="mr-2 h-5 w-5" />
                Check Your Symptoms
              </Button>
            </Link>
            <Link to="/chat-ai">
              <Button size="lg" variant="outline">
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
