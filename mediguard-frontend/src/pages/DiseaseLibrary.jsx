
import React, { useState } from 'react';
import { Helmet } from 'react-helmet';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Search, TrendingUp, AlertTriangle } from 'lucide-react';
import { diseases } from '@/data/diseases';

const DiseaseLibrary = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [severityFilter, setSeverityFilter] = useState('All');
  const [commonOnly, setCommonOnly] = useState(false);

  const categories = ['All', ...new Set(diseases.map(d => d.category))];
  const severities = ['All', 'Low', 'Medium', 'High'];

  const filteredDiseases = diseases.filter((disease) => {
    const matchesSearch = disease.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          disease.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          disease.symptoms.some(s => s.toLowerCase().includes(searchQuery.toLowerCase()));
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
        <title>Disease Library - MediGuard Bamenda</title>
        <meta name="description" content="Comprehensive library of diseases. Learn about symptoms, prevention, and treatment." />
      </Helmet>

      <div className="min-h-screen bg-muted/30 py-12">
        <div className="container mx-auto px-4 max-w-7xl">
          <div className="text-center mb-8 flex flex-col items-center">
            <div className="mb-4">
              <img 
                src="/public/mediguard.png" 
                alt="MediGuard Logo" 
                className="logo-sm"
              />
            </div>
            <h1 className="text-4xl font-bold mb-4">Disease Library</h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Explore comprehensive information about diseases and health conditions
            </p>
          </div>

          <Card className="mb-8">
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="relative md:col-span-2">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                  <Input
                    type="text"
                    placeholder="Search by name, symptom, or description..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 text-gray-900 bg-white"
                  />
                </div>
                
                <div>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-white px-3 py-2 text-sm text-gray-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={categoryFilter}
                    onChange={(e) => setCategoryFilter(e.target.value)}
                  >
                    {categories.map(c => <option key={c} value={c}>Category: {c}</option>)}
                  </select>
                </div>

                <div>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-white px-3 py-2 text-sm text-gray-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={severityFilter}
                    onChange={(e) => setSeverityFilter(e.target.value)}
                  >
                    {severities.map(s => <option key={s} value={s}>Severity: {s}</option>)}
                  </select>
                </div>

                <div className="md:col-span-4 flex items-center space-x-2">
                  <Checkbox
                    id="common-filter"
                    checked={commonOnly}
                    onCheckedChange={(checked) => setCommonOnly(checked)}
                  />
                  <Label htmlFor="common-filter" className="text-sm font-medium cursor-pointer">
                    Show only diseases common in Bamenda
                  </Label>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredDiseases.map((disease) => (
              <Link key={disease.id} to={`/disease/${disease.id}`}>
                <Card className="h-full hover:shadow-2xl transition-all duration-300 cursor-pointer border-2 hover:border-primary/50 flex flex-col">
                  <CardHeader className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <div className="px-3 py-1 rounded-full text-sm font-semibold bg-primary/10 text-primary">
                        {disease.name}
                      </div>
                      {disease.severity.toLowerCase() === 'high' && (
                        <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0 ml-2" />
                      )}
                    </div>
                    <CardDescription className="text-foreground/80">
                      {disease.description}
                    </CardDescription>
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

          {filteredDiseases.length === 0 && (
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
