import React, { useEffect, useState } from 'react';
import { Helmet } from 'react-helmet';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Shield, Brain, AlertCircle, Users, Thermometer, Activity, Stethoscope, Bot, MessageCircle, BookOpen, Database, TrendingUp, Megaphone, Droplets, HandHeart } from 'lucide-react';
import NearbyFacilities from '@/components/NearbyFacilities';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { getAnalyticsSummary, getDiseases, getOutbreakAlerts, getTopDiseases, getTrends } from '@/services/api';

const HomePage = () => {
  const [featuredDiseases, setFeaturedDiseases] = useState([]);
  const [summary, setSummary] = useState({
    diseases_tracked: 19,
    total_predictions: 0,
    top_disease: 'Malaria',
  });
  const [topDiseases, setTopDiseases] = useState([]);
  const [weeklyTrends, setWeeklyTrends] = useState([]);
  const [outbreakInfo, setOutbreakInfo] = useState({ alerts: [], rainy_season: false, has_alerts: false });
  
  const trustIndicators = [
    {
      icon: Users,
      title: 'Community-Focused',
      description: 'Built specifically for the Bamenda community, understanding local health challenges and needs.',
    },
    {
      icon: Brain,
      title: 'AI-Powered',
      description: 'Advanced artificial intelligence analyzes symptoms to provide accurate disease predictions.',
    },
    {
      icon: AlertCircle,
      title: 'Early Detection',
      description: 'Catch potential health issues early with our comprehensive symptom analysis system.',
    },
    {
      icon: Shield,
      title: 'Trustworthy Care',
      description: 'Reliable, modern, and accessible health screening available 24/7 for everyone in our community.',
    },
  ];

  const howItWorks = [
    {
      step: 1,
      title: 'Select Symptoms',
      description: 'Choose from organized categories of symptoms you are experiencing.',
      icon: Thermometer,
    },
    {
      step: 2,
      title: 'AI Analysis',
      description: 'Our intelligent system analyzes your symptoms and health indicators.',
      icon: Brain,
    },
    {
      step: 3,
      title: 'Get Predictions',
      description: 'Receive potential disease matches with confidence levels and severity.',
      icon: Activity,
    },
    {
      step: 4,
      title: 'Take Action',
      description: 'Follow personalized health advice and recommendations for next steps.',
      icon: Stethoscope,
    },
  ];

  const fallbackDiseases = [
    {
      name: 'Malaria',
      description: 'Common mosquito-borne disease prevalent in Bamenda, causing fever, chills, and fatigue.',
      color: 'bg-red-100 text-red-800',
    },
    {
      name: 'Typhoid Fever',
      description: 'Bacterial infection transmitted through contaminated food and water, causing high fever.',
      color: 'bg-orange-100 text-orange-800',
    },
    {
      name: 'Respiratory Infections',
      description: 'Common infections affecting the airways, often causing cough and breathing difficulties.',
      color: 'bg-blue-100 text-blue-800',
    },
    {
      name: 'Cholera',
      description: 'Waterborne disease causing severe diarrhea and dehydration, requiring immediate attention.',
      color: 'bg-purple-100 text-purple-800',
    },
  ];

  const sensitizationTips = [
    {
      title: 'Malaria prevention',
      body: 'Sleep under treated mosquito nets, clear stagnant water, and seek testing early for fever with chills.',
      icon: Shield,
      tone: 'text-emerald-700 bg-emerald-50 border-emerald-200 dark:bg-emerald-950/20 dark:border-emerald-900/50',
    },
    {
      title: 'Safe water habits',
      body: 'Boil, filter, or treat drinking water. Wash hands before meals and after using the toilet.',
      icon: Droplets,
      tone: 'text-sky-700 bg-sky-50 border-sky-200 dark:bg-sky-950/20 dark:border-sky-900/50',
    },
    {
      title: 'Act early',
      body: 'Persistent fever, breathing difficulty, severe dehydration, bleeding, or pregnancy warning signs need prompt care.',
      icon: HandHeart,
      tone: 'text-amber-700 bg-amber-50 border-amber-200 dark:bg-amber-950/20 dark:border-amber-900/50',
    },
  ];

  useEffect(() => {
    getDiseases({ featured: true })
      .then((res) => {
        if (Array.isArray(res.data) && res.data.length) {
          setFeaturedDiseases(res.data.slice(0, 4));
        } else {
          setFeaturedDiseases(fallbackDiseases);
        }
      })
      .catch(() => setFeaturedDiseases(fallbackDiseases));

    getAnalyticsSummary()
      .then((res) => setSummary((current) => ({ ...current, ...res.data })))
      .catch(() => {});

    getTopDiseases()
      .then((res) => setTopDiseases(Array.isArray(res.data) ? res.data.slice(0, 3) : []))
      .catch(() => setTopDiseases([]));

    getTrends()
      .then((res) => setWeeklyTrends(Array.isArray(res.data) ? res.data.slice(-4) : []))
      .catch(() => setWeeklyTrends([]));

    getOutbreakAlerts()
      .then((res) => setOutbreakInfo(res.data || { alerts: [], rainy_season: false, has_alerts: false }))
      .catch(() => {});
  }, []);

  const staggerContainer = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15
      }
    }
  };

  const fadeUpItem = {
    hidden: { opacity: 0, y: 30 },
    show: { opacity: 1, y: 0, transition: { duration: 0.5 } }
  };

  return (
    <>
      <Helmet>
        <title>MediGuard Bamenda - Community Health Screening</title>
        <meta name="description" content="AI-powered early disease detection system for the Bamenda community. Check symptoms, explore diseases, and get personalized health guidance." />
      </Helmet>

      <div className="min-h-screen flex flex-col">
        {/* Hero Section */}
        <section className="relative min-h-[92vh] flex items-center justify-center overflow-hidden py-12 sm:py-16">
          {/* Background Image: Professional Healthcare Image */}
          <div
            className="absolute inset-0 bg-cover bg-center bg-no-repeat z-0"
            style={{ backgroundImage: 'url(/hero.jpeg)' }}
          >
            {/* Subtle dark overlay for text readability */}
            <div className="absolute inset-0 bg-black/40"></div>
          </div>

          <div className="container mx-auto px-4 z-10 relative flex flex-col items-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="mb-4 sm:mb-8"
            >
              <img 
                src="/mediguard.png" 
                alt="MediGuard Logo" 
                className="h-20 sm:logo-lg w-auto object-contain drop-shadow-2xl brightness-0 invert" 
              />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
              className="text-center max-w-4xl mx-auto"
            >
              <h1 className="text-3xl sm:text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-4 sm:mb-6 leading-tight drop-shadow-lg tracking-tight text-balance">
                Smart Diagnosis - Fast Care - Safe Health
              </h1>
              <p className="text-sm sm:text-lg md:text-xl text-gray-100 mb-6 sm:mb-8 max-w-2xl mx-auto drop-shadow-md font-medium">
                AI-powered early disease detection for Bamenda, combining symptom prediction, encyclopedia-grounded chat, disease education, and local trend monitoring.
              </p>
              
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-3 sm:gap-4 w-full max-w-sm sm:max-w-none mx-auto">
                {/* Get Started Button */}
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Link to="/symptom-checker" className="block">
                    <Button size="lg" className="w-full sm:w-auto text-base sm:text-lg px-6 sm:px-8 py-5 sm:py-6 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold shadow-xl transition-all border border-transparent">
                      Get Started
                      <ArrowRight className="ml-2 h-5 w-5" />
                    </Button>
                  </Link>
                </motion.div>
                
                {/* Try MediGuard AI Button - NEW */}
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Link to="/chat-ai" className="block">
                    <Button 
                      size="lg" 
                      className="w-full sm:w-auto text-base sm:text-lg px-6 sm:px-8 py-5 sm:py-6 bg-secondary hover:bg-secondary/90 text-white font-semibold shadow-xl transition-all border border-white/20 backdrop-blur-sm"
                    >
                      <Bot className="mr-2 h-5 w-5" />
                      Try MediGuard AI
                      <MessageCircle className="ml-2 h-5 w-5" />
                    </Button>
                  </Link>
                </motion.div>
                
                {/* Learn More Button */}
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Link to="/disease-library" className="block">
                    <Button size="lg" variant="outline" className="w-full sm:w-auto text-base sm:text-lg px-6 sm:px-8 py-5 sm:py-6 bg-white/10 hover:bg-white/20 text-white border-white/30 backdrop-blur-sm font-semibold shadow-xl transition-all">
                      Learn More
                    </Button>
                  </Link>
                </motion.div>
              </div>

              {/* Quick Access Badges - Optional */}
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.5 }}
                className="flex flex-wrap items-center justify-center gap-3 mt-8"
              >
                <span className="text-sm text-white/80">Live MediGuard coverage:</span>
                <Link to="/chat-ai">
                  <span className="inline-flex items-center gap-1 px-3 py-1 bg-white/20 backdrop-blur-sm rounded-full text-sm text-white hover:bg-white/30 transition-colors">
                    <Bot className="h-3 w-3" /> Symptom chat
                  </span>
                </Link>
                <Link to="/disease-library">
                  <span className="inline-flex items-center gap-1 px-3 py-1 bg-white/20 backdrop-blur-sm rounded-full text-sm text-white hover:bg-white/30 transition-colors">
                    <BookOpen className="h-3 w-3" /> {summary.diseases_tracked} diseases
                  </span>
                </Link>
              </motion.div>
            </motion.div>
          </div>

          {/* Scroll Indicator */}
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 1, repeat: Infinity, repeatType: "reverse" }}
            className="absolute bottom-8 left-1/2 transform -translate-x-1/2 text-white/80"
          >
            <div className="w-6 h-10 border-2 border-white/30 rounded-full flex justify-center">
              <div className="w-1 h-2 bg-white/60 rounded-full mt-2"></div>
            </div>
          </motion.div>
        </section>

        {/* Trust Indicators - 2 columns on mobile, 3 columns on desktop */}
        <section className="py-16 sm:py-20 bg-background">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 sm:gap-4 mb-10">
              {[
                { label: 'Diseases in Library', value: summary.diseases_tracked, icon: BookOpen },
                { label: 'Recorded Screenings', value: summary.total_predictions, icon: Activity },
                { label: 'Most Reported', value: summary.top_disease, icon: Database },
              ].map((item) => (
                <Card key={item.label} className="medical-panel">
                  <CardContent className="p-2.5 sm:p-5 flex flex-col sm:flex-row items-center text-center sm:text-left gap-2 sm:gap-4 min-h-[116px] sm:min-h-0">
                    <div className="h-9 w-9 sm:h-11 sm:w-11 rounded-lg bg-primary/10 text-primary flex items-center justify-center flex-shrink-0">
                      <item.icon className="h-4 w-4 sm:h-5 sm:w-5" />
                    </div>
                    <div className="min-w-0 w-full">
                      <p className="text-[10px] sm:text-sm text-muted-foreground leading-tight">{item.label}</p>
                      <p className="text-sm sm:text-xl font-bold truncate">{item.value}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
            
            {/* Trust Indicators Cards - 2 columns on mobile, 4 on desktop */}
            <motion.div 
              variants={staggerContainer}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, margin: "-100px" }}
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
            >
              {trustIndicators.map((indicator, index) => (
                <motion.div key={index} variants={fadeUpItem} whileHover={{ y: -5, transition: { duration: 0.2 } }}>
                  <Card className="h-full hover:shadow-xl transition-all duration-300 medical-panel">
                    <CardHeader>
                      <div className="w-14 h-14 bg-primary/10 rounded-xl flex items-center justify-center mb-4 text-primary shadow-sm">
                        <indicator.icon className="h-7 w-7" />
                      </div>
                      <CardTitle className="text-xl">{indicator.title}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-muted-foreground">{indicator.description}</p>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* Community Trends & Sensitization */}
        <section className="py-16 sm:py-20 bg-muted/30 border-y">
          <div className="container mx-auto px-4">
            <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className="rounded-lg border bg-background p-5 sm:p-6 shadow-sm"
              >
                <div className="mb-5 flex items-start justify-between gap-4">
                  <div>
                    <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-sm font-semibold text-primary">
                      <TrendingUp className="h-4 w-4" />
                      Community trends
                    </div>
                    <h2 className="text-2xl sm:text-3xl font-bold">What MediGuard is seeing</h2>
                    <p className="mt-2 text-sm text-muted-foreground">
                      A quick view from recent screenings and local seasonal risk signals.
                    </p>
                  </div>
                  <Link to="/trends">
                    <Button variant="outline" size="sm">View dashboard</Button>
                  </Link>
                </div>

                <div className="grid grid-cols-3 gap-2 sm:gap-3">
                  <Card>
                    <CardContent className="p-3 text-center min-h-[94px] flex flex-col justify-center">
                      <p className="text-[10px] sm:text-xs text-muted-foreground">This week</p>
                      <p className="text-lg sm:text-2xl font-bold text-primary">{summary.active_this_week || 0}</p>
                      <p className="text-[10px] sm:text-xs text-muted-foreground">screenings</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-3 text-center min-h-[94px] flex flex-col justify-center">
                      <p className="text-[10px] sm:text-xs text-muted-foreground">Top report</p>
                      <p className="text-sm sm:text-lg font-bold truncate">{summary.top_disease || 'No data'}</p>
                      <p className="text-[10px] sm:text-xs text-muted-foreground">{summary.top_disease_count || 0} cases</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-3 text-center min-h-[94px] flex flex-col justify-center">
                      <p className="text-[10px] sm:text-xs text-muted-foreground">Risk watch</p>
                      <p className="text-sm sm:text-lg font-bold truncate">{outbreakInfo.has_alerts ? 'Active' : outbreakInfo.rainy_season ? 'Rainy' : 'Stable'}</p>
                      <p className="text-[10px] sm:text-xs text-muted-foreground">status</p>
                    </CardContent>
                  </Card>
                </div>

                <div className="mt-5 space-y-3">
                  {(topDiseases.length ? topDiseases : [
                    { name: 'Malaria', count: 120 },
                    { name: 'Typhoid Fever', count: 96 },
                    { name: 'Pneumonia', count: 82 },
                  ]).map((item, index) => {
                    const max = Math.max(...(topDiseases.length ? topDiseases : [{ count: 120 }]).map(row => row.count || row.cases || 1));
                    const count = item.count || item.cases || 0;
                    return (
                      <div key={item.name || item.disease || index}>
                        <div className="mb-1 flex items-center justify-between text-sm">
                          <span className="font-semibold">{item.name || item.disease}</span>
                          <span className="text-muted-foreground">{count}</span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-muted">
                          <motion.div
                            className="h-full rounded-full bg-primary"
                            initial={{ width: 0 }}
                            whileInView={{ width: `${Math.max(12, (count / max) * 100)}%` }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.8, delay: index * 0.1 }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>

                {weeklyTrends.length > 0 && (
                  <p className="mt-4 text-xs text-muted-foreground">
                    Latest trend point: {weeklyTrends[weeklyTrends.length - 1].disease} had {weeklyTrends[weeklyTrends.length - 1].count} report(s).
                  </p>
                )}
              </motion.div>

              <motion.div
                variants={staggerContainer}
                initial="hidden"
                whileInView="show"
                viewport={{ once: true }}
                className="grid gap-4"
              >
                <div>
                  <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-secondary/10 px-3 py-1 text-sm font-semibold text-secondary">
                    <Megaphone className="h-4 w-4" />
                    Health sensitization
                  </div>
                  <h2 className="text-2xl sm:text-3xl font-bold">Simple actions that reduce risk</h2>
                </div>

                {outbreakInfo.has_alerts && (
                  <Card className="border-red-200 bg-red-50 dark:border-red-900/50 dark:bg-red-950/20">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
                        <div>
                          <p className="font-bold text-red-800 dark:text-red-300">Community watch alert</p>
                          <p className="text-sm text-red-700 dark:text-red-300">
                            {outbreakInfo.alerts?.[0]?.disease || 'A condition'} is showing increased reports. Follow prevention guidance and seek care early.
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Sensitization Tips - 2 columns on mobile, 1 on desktop */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-3">
                  {sensitizationTips.map((tip) => (
                    <motion.div key={tip.title} variants={fadeUpItem}>
                      <Card className={`h-full border ${tip.tone}`}>
                        <CardContent className="p-4">
                          <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-background/80">
                            <tip.icon className="h-5 w-5" />
                          </div>
                          <h3 className="font-bold">{tip.title}</h3>
                          <p className="mt-1 text-sm leading-relaxed">{tip.body}</p>
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            </div>
          </div>
        </section>

        {/* How It Works - 2 columns on mobile, 4 on desktop */}
        <section className="py-16 sm:py-24 bg-muted/30 border-y">
          <div className="container mx-auto px-4">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center mb-16"
            >
              <h2 className="text-3xl sm:text-4xl font-bold mb-4">How MediGuard Works</h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Simple, fast, and accurate health screening in just four easy steps
              </p>
            </motion.div>
            <motion.div 
              variants={staggerContainer}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true }}
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 relative"
            >
              <div className="hidden lg:block absolute top-8 left-[12%] right-[12%] h-1 bg-gradient-to-r from-primary/10 via-primary/40 to-primary/10 rounded-full z-0"></div>
              {howItWorks.map((step, index) => (
                <motion.div key={index} variants={fadeUpItem} className="relative z-10">
                  <div className="flex flex-col items-center text-center group">
                    <motion.div 
                      whileHover={{ scale: 1.1, rotate: 5 }}
                      className="w-16 h-16 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-2xl font-bold mb-6 shadow-lg border-4 border-background group-hover:bg-secondary transition-colors"
                    >
                      {step.step}
                    </motion.div>
                    <div className="w-12 h-12 bg-background shadow-sm rounded-lg flex items-center justify-center mb-4 border border-border group-hover:border-primary/50 transition-colors">
                      <step.icon className="h-6 w-6 text-primary group-hover:text-secondary transition-colors" />
                    </div>
                    <h3 className="text-xl font-semibold mb-2">{step.title}</h3>
                    <p className="text-muted-foreground">{step.description}</p>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* Featured Diseases - 2 columns on mobile, 4 on desktop */}
        <section className="py-16 sm:py-24 bg-background">
          <div className="container mx-auto px-4">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center mb-12"
            >
              <h2 className="text-3xl sm:text-4xl font-bold mb-4">Common Diseases in Bamenda</h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Learn about the most prevalent health conditions in our community
              </p>
            </motion.div>
            <motion.div 
              variants={staggerContainer}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true }}
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
            >
              {(featuredDiseases.length ? featuredDiseases : fallbackDiseases).map((disease, index) => (
                <motion.div key={disease.slug || disease.name || index} variants={fadeUpItem}>
                  <Card className="h-full hover:shadow-xl transition-all duration-300 border border-border hover:border-primary/50 group flex flex-col">
                    <CardHeader>
                      <div className="inline-block px-3 py-1 rounded-full text-sm font-semibold mb-3 bg-primary/10 text-primary w-fit">
                        {disease.name}
                      </div>
                      <CardTitle className="text-base font-semibold">{disease.category || 'General'} - {disease.severity || 'Medium'}</CardTitle>
                      <CardDescription className="text-foreground/80 text-base leading-relaxed">
                        {disease.description}
                      </CardDescription>
                      {Array.isArray(disease.symptoms) && (
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          Key symptoms: {disease.symptoms.slice(0, 4).join(', ')}
                        </p>
                      )}
                    </CardHeader>
                    <CardContent className="mt-auto pt-4 border-t border-border/50">
                      <Link to={`/disease/${disease.slug || disease.id || ''}`}>
                        <Button variant="ghost" className="w-full group-hover:bg-primary/10 group-hover:text-primary transition-all duration-300 font-medium">
                          View Details <ArrowRight className="ml-2 h-4 w-4" />
                        </Button>
                      </Link>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </motion.div>

            {/* AI Assistant CTA */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="mt-16 text-center"
            >
              <div className="flex flex-col sm:flex-row items-center gap-4 p-6 bg-card rounded-lg border border-primary/20 shadow-sm max-w-3xl mx-auto">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
                  <Bot className="h-8 w-8 text-primary" />
                </div>
                <div className="text-left">
                  <h3 className="text-2xl font-bold mb-2">Have questions? Talk to our AI assistant</h3>
                  <p className="text-muted-foreground mb-3">
                    Get instant answers about symptoms, diseases, and health recommendations
                  </p>
                  <Link to="/chat-ai">
                    <Button className="bg-secondary hover:bg-secondary/90 text-white">
                      <MessageCircle className="mr-2 h-4 w-4" />
                      Start AI Chat
                    </Button>
                  </Link>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Nearby Health Facilities - Expanded on desktop/laptop */}
        <section className="py-16 sm:py-20 bg-muted/30 border-t">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
            >
              <NearbyFacilities compact={false} />
            </motion.div>
          </div>
        </section>
      </div>
    </>
  );
};

export default HomePage;