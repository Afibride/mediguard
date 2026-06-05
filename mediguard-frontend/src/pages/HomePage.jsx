import React, { useEffect, useState, useRef } from 'react';
import { Helmet } from 'react-helmet';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Shield, Brain, AlertCircle, Users, Thermometer, Activity, Stethoscope, Bot, MessageCircle, BookOpen, Database, TrendingUp, Megaphone, Droplets, HandHeart, ChevronLeft, ChevronRight, Play, Pause, X, Heart } from 'lucide-react';
import NearbyFacilities from '@/components/NearbyFacilities';
import NewsletterSignup from '@/components/NewsletterSignup';
import SeasonalBanner from '@/components/SeasonalBanner';
import { useLanguage } from '@/contexts/LanguageContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { getAnalyticsSummary, getDiseases, getOutbreakAlerts, getTopDiseases, getTrends } from '@/services/api';

// Auto-scroll Carousel Component
const AutoScrollCarousel = ({ children, items, title, viewAllLink, className = "", cardWidth = 280 }) => {
  const scrollContainerRef = useRef(null);
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(false);
  const [isPlaying, setIsPlaying] = useState(true);
  const autoScrollInterval = useRef(null);
  const [activeIndex, setActiveIndex] = useState(0);

  const updateArrows = () => {
    if (scrollContainerRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollContainerRef.current;
      setShowLeftArrow(scrollLeft > 10);
      setShowRightArrow(scrollLeft + clientWidth < scrollWidth - 10);
      const firstItem = scrollContainerRef.current.children[0];
      if (firstItem) {
        const itemWidth = firstItem.offsetWidth + 12;
        setActiveIndex(Math.min(items.length - 1, Math.max(0, Math.round(scrollLeft / itemWidth))));
      }
    }
  };

  const scroll = (direction) => {
    if (scrollContainerRef.current) {
      const scrollAmount = scrollContainerRef.current.clientWidth * 0.8;
      const newScrollLeft = direction === 'left' 
        ? scrollContainerRef.current.scrollLeft - scrollAmount
        : scrollContainerRef.current.scrollLeft + scrollAmount;
      
      scrollContainerRef.current.scrollTo({
        left: newScrollLeft,
        behavior: 'smooth'
      });
    }
  };

  const startAutoScroll = () => {
    if (autoScrollInterval.current) clearInterval(autoScrollInterval.current);
    autoScrollInterval.current = setInterval(() => {
      if (scrollContainerRef.current && isPlaying && items.length > 1) {
        const { scrollLeft, scrollWidth, clientWidth } = scrollContainerRef.current;
        const maxScroll = scrollWidth - clientWidth;
        
        if (scrollLeft + clientWidth >= maxScroll - 5) {
          scrollContainerRef.current.scrollTo({ left: 0, behavior: 'smooth' });
        } else {
          const itemWidth = scrollContainerRef.current.children[0]?.offsetWidth || clientWidth * 0.8;
          scrollContainerRef.current.scrollBy({ left: itemWidth + 12, behavior: 'smooth' });
        }
      }
    }, 3500);
  };

  const stopAutoScroll = () => {
    if (autoScrollInterval.current) {
      clearInterval(autoScrollInterval.current);
      autoScrollInterval.current = null;
    }
  };

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (container) {
      container.addEventListener('scroll', updateArrows);
      window.addEventListener('resize', updateArrows);
      updateArrows();
      startAutoScroll();
    }
    return () => {
      if (container) container.removeEventListener('scroll', updateArrows);
      window.removeEventListener('resize', updateArrows);
      stopAutoScroll();
    };
  }, [items.length]);

  useEffect(() => {
    if (isPlaying) {
      startAutoScroll();
    } else {
      stopAutoScroll();
    }
  }, [isPlaying]);

  const toggleAutoScroll = () => {
    setIsPlaying(!isPlaying);
  };

  return (
    <div className={`relative ${className}`}>
      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          {title && <h3 className="text-base font-semibold">{title}</h3>}
          {viewAllLink && (
            <Link to={viewAllLink} className="text-xs text-primary hover:underline hidden sm:block">
              View all →
            </Link>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={toggleAutoScroll}
            className="p-1.5 rounded-full bg-muted hover:bg-primary/20 transition-colors"
            aria-label={isPlaying ? "Pause auto-scroll" : "Play auto-scroll"}
          >
            {isPlaying ? <Pause className="h-3 w-3" /> : <Play className="h-3 w-3" />}
          </button>
          <button
            onClick={() => scroll('left')}
            className={`p-1.5 rounded-full bg-muted hover:bg-primary/20 transition-colors ${!showLeftArrow && 'opacity-30 cursor-not-allowed'}`}
            disabled={!showLeftArrow}
            aria-label="Previous"
          >
            <ChevronLeft className="h-3 w-3" />
          </button>
          <button
            onClick={() => scroll('right')}
            className={`p-1.5 rounded-full bg-muted hover:bg-primary/20 transition-colors ${!showRightArrow && 'opacity-30 cursor-not-allowed'}`}
            disabled={!showRightArrow}
            aria-label="Next"
          >
            <ChevronRight className="h-3 w-3" />
          </button>
        </div>
      </div>
      
      <div
        ref={scrollContainerRef}
        className="flex overflow-x-auto gap-3 pb-3 scrollbar-hide snap-x snap-mandatory"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        onMouseEnter={stopAutoScroll}
        onMouseLeave={startAutoScroll}
        onTouchStart={stopAutoScroll}
        onTouchEnd={startAutoScroll}
      >
        {children}
      </div>
      
      {viewAllLink && (
        <div className="mt-2 text-center">
          <Link to={viewAllLink} className="text-xs text-primary hover:underline inline-flex items-center gap-1">
            View all {title?.toLowerCase()} <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
      )}
      
      {items.length > 1 && (
        <div className="flex justify-center gap-1 mt-2">
          {items.map((_, idx) => (
            <button
              key={idx}
              className={`h-1 rounded-full transition-all duration-300 ${
                idx === activeIndex ? 'w-4 bg-primary' : 'w-1 bg-muted-foreground/30'
              }`}
              onClick={() => {
                if (scrollContainerRef.current) {
                  const itemWidth = scrollContainerRef.current.children[0]?.offsetWidth || cardWidth;
                  scrollContainerRef.current.scrollTo({
                    left: idx * (itemWidth + 12),
                    behavior: 'smooth'
                  });
                  setActiveIndex(idx);
                }
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Add global styles for hiding scrollbar
const style = document.createElement('style');
style.textContent = `
  .scrollbar-hide::-webkit-scrollbar {
    display: none;
  }
`;
document.head.appendChild(style);

const HomePage = () => {
  const { t } = useLanguage();
  const [featuredDiseases, setFeaturedDiseases] = useState([]);
  const [summary, setSummary] = useState({
    diseases_tracked: 19,
    total_predictions: 0,
    top_disease: 'Malaria',
  });
  const [topDiseases, setTopDiseases] = useState([]);
  const [weeklyTrends, setWeeklyTrends] = useState([]);
  const [outbreakInfo, setOutbreakInfo] = useState({ alerts: [], rainy_season: false, has_alerts: false });
  // STD banner: dismissable only for the current session — always returns on next visit
  const [showStdBanner, setShowStdBanner] = useState(
    () => sessionStorage.getItem('mg_stdBannerHidden') !== '1'
  );

  // Auto-dismiss STI banner after 10 seconds
  useEffect(() => {
    if (!showStdBanner) return;
    const timer = setTimeout(() => setShowStdBanner(false), 10000);
    return () => clearTimeout(timer);
  }, [showStdBanner]);
  
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
      slug: 'malaria',
      id: 'malaria',
      category: 'Mosquito-borne',
      severity: 'High',
      symptoms: ['Fever', 'Chills', 'Headache', 'Fatigue']
    },
    {
      name: 'Typhoid Fever',
      description: 'Bacterial infection transmitted through contaminated food and water, causing high fever.',
      color: 'bg-orange-100 text-orange-800',
      slug: 'typhoid-fever',
      id: 'typhoid-fever',
      category: 'Bacterial',
      severity: 'High',
      symptoms: ['Prolonged fever', 'Headache', 'Abdominal pain', 'Constipation']
    },
    {
      name: 'Respiratory Infections',
      description: 'Common infections affecting the airways, often causing cough and breathing difficulties.',
      color: 'bg-blue-100 text-blue-800',
      slug: 'respiratory-infections',
      id: 'respiratory-infections',
      category: 'Respiratory',
      severity: 'Medium',
      symptoms: ['Cough', 'Fever', 'Shortness of breath', 'Chest congestion']
    },
    {
      name: 'Cholera',
      description: 'Waterborne disease causing severe diarrhea and dehydration, requiring immediate attention.',
      color: 'bg-purple-100 text-purple-800',
      slug: 'cholera',
      id: 'cholera',
      category: 'Waterborne',
      severity: 'Critical',
      symptoms: ['Severe diarrhea', 'Vomiting', 'Dehydration', 'Leg cramps']
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
        <title>MediGuard Bamenda — AI Health Screening & Disease Detection</title>
        <meta name="description" content="AI-powered early disease detection for the Bamenda community. Check symptoms, explore diseases, get personalized guidance, and find nearby health facilities — free, 24/7." />
        <meta name="keywords" content="MediGuard, symptom checker, Bamenda health, disease detection, malaria, typhoid, AI health assistant, Cameroon community health" />
        <link rel="canonical" href="https://mediguard.info/" />
        {/* Open Graph */}
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://mediguard.info/" />
        <meta property="og:title" content="MediGuard Bamenda — AI Health Screening & Disease Detection" />
        <meta property="og:description" content="AI-powered early disease detection for the Bamenda community. Check symptoms, explore diseases, and get personalized health guidance." />
        <meta property="og:image" content="https://mediguard.info/mediguard.png" />
        <meta property="og:image:alt" content="MediGuard Logo" />
        <meta property="og:site_name" content="MediGuard" />
        {/* Twitter */}
        <meta name="twitter:card" content="summary" />
        <meta name="twitter:title" content="MediGuard Bamenda — AI Health Screening" />
        <meta name="twitter:description" content="Free AI-powered symptom checker and disease detection for Bamenda. Available 24/7." />
        <meta name="twitter:image" content="https://mediguard.info/mediguard.png" />
      </Helmet>

      <div className="min-h-screen flex flex-col overflow-x-hidden">
        {/* Hero Section */}
        <section className="relative min-h-[92vh] flex items-center justify-center overflow-hidden py-12 sm:py-16">
          <div
            className="absolute inset-0 bg-cover bg-center bg-no-repeat z-0"
            style={{ backgroundImage: 'url(/hero.jpeg)' }}
          >
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
                {t('hero_title')}
              </h1>
              <p className="text-sm sm:text-lg md:text-xl text-gray-100 mb-6 sm:mb-8 max-w-2xl mx-auto drop-shadow-md font-medium">
                {t('hero_subtitle')}
              </p>
              
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-3 sm:gap-4 w-full max-w-sm sm:max-w-none mx-auto">
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Link to="/symptom-checker" className="block">
                    <Button size="lg" className="w-full sm:w-auto text-base sm:text-lg px-6 sm:px-8 py-5 sm:py-6 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold shadow-xl transition-all border border-transparent">
                      {t('hero_get_started')}
                      <ArrowRight className="ml-2 h-5 w-5" />
                    </Button>
                  </Link>
                </motion.div>
                
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Link to="/chat-ai" className="block">
                    <Button 
                      size="lg" 
                      className="w-full sm:w-auto text-base sm:text-lg px-6 sm:px-8 py-5 sm:py-6 bg-secondary hover:bg-secondary/90 text-white font-semibold shadow-xl transition-all border border-white/20 backdrop-blur-sm"
                    >
                      <Bot className="mr-2 h-5 w-5" />
                      {t('hero_try_ai')}
                      <MessageCircle className="ml-2 h-5 w-5" />
                    </Button>
                  </Link>
                </motion.div>
                
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Link to="/disease-library" className="block">
                    <Button size="lg" variant="outline" className="w-full sm:w-auto text-base sm:text-lg px-6 sm:px-8 py-5 sm:py-6 bg-white/10 hover:bg-white/20 text-white border-white/30 backdrop-blur-sm font-semibold shadow-xl transition-all">
                      {t('hero_learn_more')}
                    </Button>
                  </Link>
                </motion.div>
              </div>

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

        {/* ── Seasonal Health Alert Banner ─────────────────────────────────── */}
        <div className="relative z-10 isolate bg-background py-4 [backface-visibility:hidden] [transform:translateZ(0)]">
          <div className="container mx-auto px-4 max-w-7xl">
            <SeasonalBanner className="w-full" />
          </div>
        </div>

        {/* Trust Indicators - Stats Grid */}
        <section className="relative z-10 isolate bg-background py-8 sm:py-20 [backface-visibility:hidden]">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-3 gap-1.5 sm:gap-4 mb-8 sm:mb-10">
              {[
                { label: 'Diseases in Library', value: summary.diseases_tracked, icon: BookOpen },
                { label: 'Recorded Screenings', value: summary.total_predictions, icon: Activity },
                { label: 'Most Reported', value: summary.top_disease, icon: Database },
              ].map((item) => (
                <Card key={item.label} className="medical-panel min-w-0 overflow-hidden">
                  <CardContent className="p-2 sm:p-5 flex flex-col sm:flex-row items-center justify-center text-center sm:text-left gap-1.5 sm:gap-4 min-h-[104px] sm:min-h-0">
                    <div className="h-7 w-7 sm:h-11 sm:w-11 rounded-lg bg-primary/10 text-primary flex items-center justify-center flex-shrink-0">
                      <item.icon className="h-4 w-4 sm:h-5 sm:w-5" />
                    </div>
                    <div className="min-w-0 w-full">
                      <p className="text-[10px] sm:text-sm text-muted-foreground leading-tight break-words">{item.label}</p>
                      <p className="text-xs sm:text-xl font-bold break-words">{item.value}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
            
            {/* Trust Indicators Cards - Row on mobile with auto-scroll */}
            <AutoScrollCarousel 
              items={trustIndicators} 
              title="Why Choose MediGuard"
              className="block sm:hidden"
            >
              {trustIndicators.map((indicator, index) => (
                <div key={index} className="snap-center w-[260px] flex-shrink-0">
                  <Card className="h-full hover:shadow-xl transition-all duration-300 medical-panel">
                    <CardHeader className="pb-2">
                      <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center mb-2 text-primary shadow-sm">
                        <indicator.icon className="h-5 w-5" />
                      </div>
                      <CardTitle className="text-base">{indicator.title}</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <p className="text-xs text-muted-foreground">{indicator.description}</p>
                    </CardContent>
                  </Card>
                </div>
              ))}
            </AutoScrollCarousel>
            
            {/* Desktop grid layout */}
            <motion.div 
              variants={staggerContainer}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, margin: "-100px" }}
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 hidden sm:grid"
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
        <section className="py-12 sm:py-20 bg-muted/30 border-y">
          <div className="container mx-auto px-4">
            <div className="flex flex-col gap-6 lg:grid lg:grid-cols-[1fr_1.2fr]">
              
              {/* What MediGuard is seeing */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className="w-full overflow-hidden rounded-lg border bg-background p-3 shadow-sm sm:p-6"
              >
                <div className="mb-4 flex flex-col items-start justify-between gap-3 sm:flex-row sm:gap-4">
                  <div className="w-full">
                    <div className="mb-2 inline-flex max-w-full items-center gap-2 rounded-full bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary sm:px-3 sm:text-sm">
                      <TrendingUp className="h-3 w-3 sm:h-4 sm:w-4 flex-shrink-0" />
                      Community trends
                    </div>
                    <h2 className="text-lg font-bold leading-tight sm:text-3xl">What MediGuard is seeing</h2>
                    <p className="mt-1 text-xs text-muted-foreground sm:mt-2 sm:text-sm">
                      A quick view from recent screenings and local seasonal risk signals.
                    </p>
                  </div>
                  <Link to="/trends" className="w-full sm:w-auto">
                    <Button variant="outline" size="sm" className="w-full text-xs sm:w-auto">View dashboard</Button>
                  </Link>
                </div>

                {/* Stats cards - row on mobile */}
                <div className="grid grid-cols-3 gap-1.5 sm:gap-3">
                  <Card className="min-w-0 overflow-hidden">
                    <CardContent className="flex min-h-[80px] flex-col justify-center p-2 text-center sm:min-h-[94px] sm:p-3">
                      <p className="text-[10px] sm:text-xs text-muted-foreground">This week</p>
                      <p className="truncate text-base font-bold text-primary sm:text-2xl">{summary.active_this_week || 0}</p>
                      <p className="text-[10px] sm:text-xs text-muted-foreground">screenings</p>
                    </CardContent>
                  </Card>
                  <Card className="min-w-0 overflow-hidden">
                    <CardContent className="flex min-h-[80px] min-w-0 flex-col justify-center p-2 text-center sm:min-h-[94px] sm:p-3">
                      <p className="text-[10px] sm:text-xs text-muted-foreground">Top report</p>
                      <p className="truncate text-xs font-bold sm:text-lg">{summary.top_disease || 'No data'}</p>
                      <p className="text-[10px] sm:text-xs text-muted-foreground">{summary.top_disease_count || 0} cases</p>
                    </CardContent>
                  </Card>
                  <Card className="min-w-0 overflow-hidden">
                    <CardContent className="flex min-h-[80px] min-w-0 flex-col justify-center p-2 text-center sm:min-h-[94px] sm:p-3">
                      <p className="text-[10px] sm:text-xs text-muted-foreground">Risk watch</p>
                      <p className="truncate text-xs font-bold sm:text-lg">{outbreakInfo.has_alerts ? 'Active' : outbreakInfo.rainy_season ? 'Rainy' : 'Stable'}</p>
                      <p className="text-[10px] sm:text-xs text-muted-foreground">status</p>
                    </CardContent>
                  </Card>
                </div>

                {/* Top diseases list */}
                <div className="mt-4 min-w-0 space-y-3 sm:mt-5">
                  {(topDiseases.length ? topDiseases : [
                    { name: 'Malaria', count: 120 },
                    { name: 'Typhoid Fever', count: 96 },
                    { name: 'Pneumonia', count: 82 },
                  ]).map((item, index) => {
                    const max = Math.max(...(topDiseases.length ? topDiseases : [{ count: 120 }]).map(row => row.count || row.cases || 1));
                    const count = item.count || item.cases || 0;
                    return (
                      <div key={item.name || item.disease || index}>
                        <div className="mb-1 flex min-w-0 items-center justify-between gap-2 text-xs sm:gap-3 sm:text-sm">
                          <span className="min-w-0 truncate font-semibold">{item.name || item.disease}</span>
                          <span className="flex-shrink-0 text-muted-foreground">{count}</span>
                        </div>
                        <div className="h-1.5 overflow-hidden rounded-full bg-muted sm:h-2">
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
                  <p className="mt-3 break-words text-[10px] text-muted-foreground sm:mt-4 sm:text-xs">
                    Latest trend point: {weeklyTrends[weeklyTrends.length - 1].disease} had {weeklyTrends[weeklyTrends.length - 1].count} report(s).
                  </p>
                )}
              </motion.div>

              {/* Right side - Health sensitization with compact cards */}
              <motion.div
                variants={staggerContainer}
                initial="hidden"
                whileInView="show"
                viewport={{ once: true }}
                className="grid min-w-0 gap-4"
              >
                <div className="min-w-0">
                  <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-secondary/10 px-2.5 py-1 text-xs font-semibold text-secondary sm:px-3 sm:text-sm">
                    <Megaphone className="h-3 w-3 sm:h-4 sm:w-4" />
                    Health sensitization
                  </div>
                  <h2 className="text-lg font-bold sm:text-2xl lg:text-3xl">Simple actions that reduce risk</h2>
                </div>

                {outbreakInfo.has_alerts && (
                  <Card className="min-w-0 overflow-hidden border-red-200 bg-red-50 dark:border-red-900/50 dark:bg-red-950/20">
                    <CardContent className="p-3 sm:p-4">
                      <div className="flex min-w-0 items-start gap-2 sm:gap-3">
                        <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-red-600 sm:h-5 sm:w-5" />
                        <div className="min-w-0">
                          <p className="text-sm font-bold text-red-800 dark:text-red-300 sm:text-base">Community watch alert</p>
                          <p className="break-words text-xs text-red-700 dark:text-red-300 sm:text-sm">
                            {outbreakInfo.alerts?.[0]?.disease || 'Malaria'} is showing increased reports. Follow prevention tips.
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Sensitization Tips - Compact horizontal scroll cards */}
                <div className="block min-w-0 sm:hidden">
                  <AutoScrollCarousel items={sensitizationTips} title="Health Tips" cardWidth={300}>
                    {sensitizationTips.map((tip) => (
                      <div key={tip.title} className="w-[82vw] max-w-[330px] flex-shrink-0 snap-start">
                        <Card className={`h-full min-w-0 border shadow-sm ${tip.tone}`}>
                          <CardContent className="p-4">
                            <div className="mb-3 flex min-w-0 items-center gap-2">
                              <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-background/80">
                                <tip.icon className="h-4 w-4" />
                              </div>
                              <h3 className="min-w-0 text-base font-bold leading-tight">{tip.title}</h3>
                            </div>
                            <p className="break-words text-sm leading-relaxed">{tip.body}</p>
                          </CardContent>
                        </Card>
                      </div>
                    ))}
                  </AutoScrollCarousel>
                </div>

                {/* Desktop grid layout */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-3 hidden sm:grid">
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

        {/* ── STD / Sexual Health Awareness Banner (MOVED HERE) ─────────────────── */}
        {showStdBanner && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            className="relative bg-gradient-to-r from-violet-700 via-purple-600 to-pink-600 text-white shadow-lg"
          >
            <div className="container mx-auto px-4 max-w-7xl py-4 sm:py-5">
              <div className="flex items-start justify-between gap-3">
                {/* Icon */}
                <div className="flex-shrink-0 mt-0.5">
                  <div className="w-9 h-9 rounded-full bg-white/15 flex items-center justify-center">
                    <Heart className="h-5 w-5 fill-white/80 text-white" />
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm sm:text-base font-bold leading-snug mb-1">
                    🛡️ Sexual Health Reminder — Protect Yourself &amp; Others from STDs/STIs
                  </p>
                  <p className="text-xs sm:text-sm text-white/90 leading-relaxed mb-3">
                    Sexually transmitted infections (STIs) including HIV, gonorrhoea, syphilis, chlamydia, and herpes
                    are <strong>preventable</strong>. Many show <strong>no symptoms</strong> — you can have one and not know it.
                    Regular testing saves lives.
                  </p>

                  {/* Protection tips grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 mb-3">
                    {[
                      { icon: '🩺', text: 'Get tested regularly — even with no symptoms' },
                      { icon: '🧰', text: 'Always use a condom correctly every time you have sex' },
                      { icon: '🚫', text: 'Abstinence is the surest way to prevent all STIs' },
                      { icon: '🤝', text: 'Be faithful to one tested, uninfected partner' },
                      { icon: '💊', text: 'Complete every treatment course if diagnosed — do not stop early' },
                      { icon: '📣', text: 'Inform your partner(s) if you test positive — they need care too' },
                    ].map(({ icon, text }) => (
                      <div key={text} className="flex items-start gap-2 text-[11px] sm:text-xs text-white/90">
                        <span className="text-sm shrink-0 leading-none mt-0.5">{icon}</span>
                        <span className="leading-relaxed">{text}</span>
                      </div>
                    ))}
                  </div>

                  <div className="flex flex-wrap items-center gap-3">
                    <Link
                      to="/disease-library"
                      className="inline-flex items-center gap-1 text-xs font-semibold bg-white/20 hover:bg-white/30 rounded-full px-3 py-1 transition-colors"
                    >
                      Learn about STIs in our Disease Library →
                    </Link>
                    <Link
                      to="/chat-ai"
                      className="inline-flex items-center gap-1 text-xs font-semibold bg-white/20 hover:bg-white/30 rounded-full px-3 py-1 transition-colors"
                    >
                      Ask MediGuard AI about protection →
                    </Link>
                  </div>
                </div>

                {/* Dismiss (session-only) */}
                <button
                  onClick={() => {
                    setShowStdBanner(false);
                    sessionStorage.setItem('mg_stdBannerHidden', '1');
                  }}
                  className="flex-shrink-0 p-1.5 rounded-full hover:bg-white/20 active:bg-white/30 transition-colors mt-0.5"
                  aria-label="Hide for this session"
                  title="Hide for this session (will show again next visit)"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {/* How It Works - Horizontal scroll on mobile */}
        <section className="py-12 sm:py-24 bg-muted/30 border-y">
          <div className="container mx-auto px-4">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center mb-8 sm:mb-12"
            >
              <h2 className="text-2xl font-bold mb-3 sm:text-4xl sm:mb-4">How MediGuard Works</h2>
              <p className="text-sm text-muted-foreground max-w-2xl mx-auto sm:text-lg">
                Simple, fast, and accurate health screening in just four easy steps
              </p>
            </motion.div>
            
            {/* Mobile horizontal scroll */}
            <div className="block sm:hidden">
              <AutoScrollCarousel items={howItWorks} cardWidth={240}>
                {howItWorks.map((step, index) => (
                  <div key={index} className="snap-start w-[240px] flex-shrink-0">
                    <div className="flex flex-col items-center text-center group p-4 bg-card rounded-xl border shadow-sm h-full">
                      <div className="w-12 h-12 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-lg font-bold mb-3 shadow-lg border-4 border-background group-hover:bg-secondary transition-colors">
                        {step.step}
                      </div>
                      <div className="w-10 h-10 bg-background shadow-sm rounded-lg flex items-center justify-center mb-2 border border-border group-hover:border-primary/50 transition-colors">
                        <step.icon className="h-5 w-5 text-primary group-hover:text-secondary transition-colors" />
                      </div>
                      <h3 className="text-base font-semibold mb-1">{step.title}</h3>
                      <p className="text-muted-foreground text-xs">{step.description}</p>
                    </div>
                  </div>
                ))}
              </AutoScrollCarousel>
            </div>
            
            {/* Desktop grid */}
            <motion.div 
              variants={staggerContainer}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true }}
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 relative hidden sm:grid"
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

        {/* Featured Diseases - Horizontal scroll on mobile */}
        <section className="py-12 sm:py-24 bg-background">
          <div className="container mx-auto px-4">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center mb-8 sm:mb-12"
            >
              <h2 className="text-2xl font-bold mb-3 sm:text-4xl sm:mb-4">Common Diseases in Bamenda</h2>
              <p className="text-sm text-muted-foreground max-w-2xl mx-auto sm:text-lg">
                Learn about the most prevalent health conditions in our community
              </p>
            </motion.div>
            
            {/* Mobile horizontal scroll */}
            <div className="block sm:hidden">
              <AutoScrollCarousel items={featuredDiseases.length ? featuredDiseases : fallbackDiseases} cardWidth={260}>
                {(featuredDiseases.length ? featuredDiseases : fallbackDiseases).map((disease, index) => (
                  <div key={disease.slug || disease.name || index} className="snap-start w-[260px] flex-shrink-0">
                    <Card className="h-full hover:shadow-xl transition-all duration-300 border border-border hover:border-primary/50 group flex flex-col">
                      <CardHeader className="pb-2">
                        <div className="inline-block px-2 py-0.5 rounded-full text-xs font-semibold mb-2 bg-primary/10 text-primary w-fit">
                          {disease.name}
                        </div>
                        <CardTitle className="text-sm font-semibold">{disease.category || 'General'} - {disease.severity || 'Medium'}</CardTitle>
                        <CardDescription className="text-foreground/80 text-xs leading-relaxed line-clamp-2">
                          {disease.description}
                        </CardDescription>
                        {Array.isArray(disease.symptoms) && (
                          <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                            Key symptoms: {disease.symptoms.slice(0, 3).join(', ')}
                          </p>
                        )}
                      </CardHeader>
                      <CardContent className="mt-auto pt-2 border-t border-border/50">
                        <Link to={`/disease/${disease.slug || disease.id || ''}`}>
                          <Button variant="ghost" size="sm" className="w-full text-xs group-hover:bg-primary/10 group-hover:text-primary transition-all duration-300">
                            View Details <ArrowRight className="ml-1 h-3 w-3" />
                          </Button>
                        </Link>
                      </CardContent>
                    </Card>
                  </div>
                ))}
              </AutoScrollCarousel>
              <div className="text-center mt-3">
                <Link to="/disease-library" className="text-xs text-primary hover:underline inline-flex items-center gap-1">
                  View all diseases <ArrowRight className="h-3 w-3" />
                </Link>
              </div>
            </div>
            
            {/* Desktop grid */}
            <motion.div 
              variants={staggerContainer}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true }}
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 hidden sm:grid"
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
              className="mt-12 text-center sm:mt-16"
            >
              <div className="flex flex-col sm:flex-row items-center gap-4 p-5 bg-card rounded-lg border border-primary/20 shadow-sm max-w-3xl mx-auto sm:p-6">
                <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center sm:w-16 sm:h-16">
                  <Bot className="h-6 w-6 text-primary sm:h-8 sm:w-8" />
                </div>
                <div className="text-center sm:text-left">
                  <h3 className="text-lg font-bold mb-1 sm:text-2xl sm:mb-2">Have questions? Talk to our AI assistant</h3>
                  <p className="text-xs text-muted-foreground mb-3 sm:text-sm sm:mb-3">
                    Get instant answers about symptoms, diseases, and health recommendations
                  </p>
                  <Link to="/chat-ai">
                    <Button className="bg-secondary hover:bg-secondary/90 text-white text-sm">
                      <MessageCircle className="mr-2 h-3 w-3 sm:h-4 sm:w-4" />
                      Start AI Chat
                    </Button>
                  </Link>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        <NewsletterSignup />

        {/* Nearby Health Facilities */}
        <section className="py-12 sm:py-20 bg-muted/30 border-t">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
            >
              <NearbyFacilities compact />
            </motion.div>
          </div>
        </section>
      </div>
    </>
  );
};

export default HomePage;
