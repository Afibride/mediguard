
import React from 'react';
import { Helmet } from 'react-helmet';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Shield, Brain, AlertCircle, Users, Thermometer, Activity, Stethoscope } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const HomePage = () => {
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

  const featuredDiseases = [
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
        <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
          {/* Background Image: Professional Healthcare Image */}
          <div
            className="absolute inset-0 bg-cover bg-center bg-no-repeat z-0"
            style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1685995833594-8c35ffa8ccb0)' }}
          >
            {/* Subtle dark overlay for text readability */}
            <div className="absolute inset-0 bg-black/40"></div>
          </div>

          <div className="container mx-auto px-4 z-10 relative flex flex-col items-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="mb-8"
            >
              <img 
                src="/public/mediguard.png" 
                alt="MediGuard Logo" 
                className="logo-lg drop-shadow-2xl brightness-0 invert" 
              />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
              className="text-center max-w-4xl mx-auto"
            >
              <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-6 leading-tight drop-shadow-lg tracking-tight">
                Smart Diagnosis • Fast Care • Safe Health
              </h1>
              <p className="text-lg md:text-xl text-gray-100 mb-10 max-w-2xl mx-auto drop-shadow-md font-medium">
                AI-powered early disease detection system designed for the Bamenda community. Get instant symptom analysis, disease predictions, and personalized health guidance.
              </p>
              
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Link to="/symptom-checker">
                    <Button size="lg" className="text-lg px-8 py-6 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold shadow-xl transition-all border border-transparent">
                      Get Started
                      <ArrowRight className="ml-2 h-5 w-5" />
                    </Button>
                  </Link>
                </motion.div>
                
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Link to="/disease-library">
                    <Button size="lg" variant="outline" className="text-lg px-8 py-6 bg-white/10 hover:bg-white/20 text-white border-white/30 backdrop-blur-sm font-semibold shadow-xl transition-all">
                      Learn More
                    </Button>
                  </Link>
                </motion.div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Trust Indicators */}
        <section className="py-20 bg-background">
          <div className="container mx-auto px-4">
            <motion.div 
              variants={staggerContainer}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, margin: "-100px" }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
            >
              {trustIndicators.map((indicator, index) => (
                <motion.div key={index} variants={fadeUpItem} whileHover={{ y: -5, transition: { duration: 0.2 } }}>
                  <Card className="h-full hover:shadow-2xl transition-all duration-300 border-2 border-border/50 bg-card">
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

        {/* How It Works */}
        <section className="py-24 bg-muted/30 border-y">
          <div className="container mx-auto px-4">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl font-bold mb-4">How MediGuard Works</h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Simple, fast, and accurate health screening in just four easy steps
              </p>
            </motion.div>
            <motion.div 
              variants={staggerContainer}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 relative"
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

        {/* Featured Diseases */}
        <section className="py-24 bg-background">
          <div className="container mx-auto px-4">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center mb-12"
            >
              <h2 className="text-4xl font-bold mb-4">Common Diseases in Bamenda</h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Learn about the most prevalent health conditions in our community
              </p>
            </motion.div>
            <motion.div 
              variants={staggerContainer}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
            >
              {featuredDiseases.map((disease, index) => (
                <motion.div key={index} variants={fadeUpItem}>
                  <Card className="h-full hover:shadow-xl transition-all duration-300 border border-border hover:border-primary/50 group flex flex-col">
                    <CardHeader>
                      <div className={`inline-block px-3 py-1 rounded-full text-sm font-semibold mb-3 ${disease.color} w-fit`}>
                        {disease.name}
                      </div>
                      <CardDescription className="text-foreground/80 text-base leading-relaxed">
                        {disease.description}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="mt-auto pt-4 border-t border-border/50">
                      <Link to="/disease-library">
                        <Button variant="ghost" className="w-full group-hover:bg-primary/10 group-hover:text-primary transition-all duration-300 font-medium">
                          Explore Library <ArrowRight className="ml-2 h-4 w-4" />
                        </Button>
                      </Link>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>
      </div>
    </>
  );
};

export default HomePage;
