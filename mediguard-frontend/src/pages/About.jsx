import React from 'react';
import { Helmet } from 'react-helmet';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Heart, Target, Users, Shield, Brain, Activity, 
  MapPin, Mail, MessageCircle, ArrowRight, Award, 
  Clock, Globe, ChevronRight, Quote, Sparkles 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const About = () => {
  const teamValues = [
    {
      icon: Heart,
      title: "Compassionate Care",
      description: "Every feature is designed with empathy, understanding that health concerns are personal and often stressful.",
      color: "text-rose-500",
      bgColor: "bg-rose-100 dark:bg-rose-900/20"
    },
    {
      icon: Target,
      title: "Community-Focused",
      description: "Built specifically for Bamenda, addressing local health challenges and cultural contexts.",
      color: "text-blue-500",
      bgColor: "bg-blue-100 dark:bg-blue-900/20"
    },
    {
      icon: Shield,
      title: "Privacy First",
      description: "Your health data stays private. We never share personal information without explicit consent.",
      color: "text-emerald-500",
      bgColor: "bg-emerald-100 dark:bg-emerald-900/20"
    },
    {
      icon: Brain,
      title: "AI-Powered",
      description: "Advanced algorithms continuously learning from medical data to provide accurate insights.",
      color: "text-purple-500",
      bgColor: "bg-purple-100 dark:bg-purple-900/20"
    }
  ];

  const impactMetrics = [
    { 
      number: "5,000+", 
      label: "Monthly Users", 
      icon: Users,
      description: "Growing community trust"
    },
    { 
      number: "50+", 
      label: "Conditions Covered", 
      icon: Activity,
      description: "Comprehensive database"
    },
    { 
      number: "24/7", 
      label: "Always Available", 
      icon: Clock,
      description: "Round-the-clock access"
    },
    { 
      number: "100%", 
      label: "Privacy Focused", 
      icon: Shield,
      description: "Your data stays yours"
    }
  ];

  const milestones = [
    {
      year: "2023",
      title: "MediGuard Founded",
      description: "Born from a need for accessible health screening in Bamenda"
    },
    {
      year: "2024",
      title: "AI Integration",
      description: "Launched AI-powered symptom checker and chat assistant"
    },
    {
      year: "2025",
      title: "Community Growth",
      description: "Serving thousands of users across the Northwest Region"
    }
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5, ease: "easeOut" }
    }
  };

  return (
    <>
      <Helmet>
        <title>About Us — MediGuard Bamenda | AI-Powered Community Health</title>
        <meta name="description" content="Learn about MediGuard Bamenda's mission to provide accessible AI-driven health screening for the Bamenda community. Discover our values, team, and commitment to privacy-first healthcare." />
        <meta property="og:title" content="About MediGuard Bamenda - Community Health Screening" />
        <meta property="og:description" content="AI-first health screening tool built for Bamenda. Free, private, and always available." />
      </Helmet>

      <div className="min-h-screen bg-gradient-to-b from-background via-background to-muted/20">
        {/* Hero Section */}
        <section className="relative py-16 md:py-24 overflow-hidden">
          {/* Background Decoration */}
          <div className="absolute inset-0 -z-10">
            <div className="absolute top-0 left-0 w-full h-96 bg-gradient-to-br from-primary/5 via-transparent to-transparent"></div>
            <div className="absolute bottom-0 right-0 w-full h-96 bg-gradient-to-tl from-secondary/5 via-transparent to-transparent"></div>
          </div>

          <div className="container mx-auto px-4 max-w-6xl">
            <motion.div 
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="text-center mb-12 md:mb-16"
            >
              {/* Logo with animation */}
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="flex justify-center mb-8"
              >
                <div className="relative">
                  <div className="absolute inset-0 bg-primary/20 rounded-full blur-3xl"></div>
                  <img 
                    src="/public/mediguard.png" 
                    alt="MediGuard Logo" 
                    className="relative logo-lg mx-auto drop-shadow-2xl" 
                  />
                </div>
              </motion.div>

              <motion.h1 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 }}
                className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 bg-gradient-to-r from-primary via-primary/80 to-secondary bg-clip-text text-transparent"
              >
                Your Health, Our Mission
              </motion.h1>

              <motion.p 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.4 }}
                className="text-lg md:text-xl text-muted-foreground max-w-3xl mx-auto mb-8 leading-relaxed"
              >
                MediGuard is an AI-first, community-focused health screening tool built to provide 
                <span className="text-primary font-semibold"> accessible symptom analysis</span> and 
                <span className="text-primary font-semibold"> early detection guidance</span> for Bamenda 
                and surrounding communities.
              </motion.p>

              {/* Location Badge */}
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4, delay: 0.5 }}
                className="flex items-center justify-center gap-2 text-sm text-muted-foreground"
              >
                <MapPin className="h-4 w-4 text-primary" />
                <span>Serving Bamenda, Northwest Region, Cameroon</span>
              </motion.div>
            </motion.div>

            {/* Impact Metrics */}
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6 mb-16 md:mb-24"
            >
              {impactMetrics.map((metric, index) => (
                <motion.div key={index} variants={itemVariants}>
                  <Card className="text-center p-4 md:p-6 border-2 hover:border-primary/50 transition-all duration-300 hover:shadow-xl bg-card/50 backdrop-blur-sm">
                    <div className="flex justify-center mb-3">
                      <div className="w-12 h-12 md:w-14 md:h-14 rounded-full bg-primary/10 flex items-center justify-center">
                        <metric.icon className="h-6 w-6 md:h-7 md:w-7 text-primary" />
                      </div>
                    </div>
                    <div className="text-xl md:text-2xl font-bold text-foreground mb-1">{metric.number}</div>
                    <div className="text-xs md:text-sm font-medium text-primary mb-1">{metric.label}</div>
                    <div className="text-xs text-muted-foreground hidden md:block">{metric.description}</div>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* Mission & Values Section */}
        <section className="py-16 md:py-24 bg-muted/30 border-y border-border">
          <div className="container mx-auto px-4 max-w-6xl">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              className="text-center mb-12"
            >
              <Badge variant="outline" className="mb-4 px-4 py-1 text-sm">
                <Sparkles className="h-3 w-3 mr-1 inline" /> Our Values
              </Badge>
              <h2 className="text-3xl md:text-4xl font-bold mb-4">What Drives Us Forward</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                Every decision we make is guided by our commitment to community health and wellbeing
              </p>
            </motion.div>

            <motion.div 
              variants={containerVariants}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
            >
              {teamValues.map((value, index) => (
                <motion.div key={index} variants={itemVariants}>
                  <Card className="h-full hover:shadow-xl transition-all duration-300 group border-2 hover:border-primary/50 bg-card/50 backdrop-blur-sm">
                    <CardHeader>
                      <div className={`w-14 h-14 rounded-xl ${value.bgColor} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                        <value.icon className={`h-7 w-7 ${value.color}`} />
                      </div>
                      <CardTitle className="text-lg md:text-xl">{value.title}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm md:text-base text-muted-foreground leading-relaxed">
                        {value.description}
                      </p>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* Our Story / Timeline */}
        <section className="py-16 md:py-24">
          <div className="container mx-auto px-4 max-w-4xl">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center mb-12"
            >
              <h2 className="text-3xl md:text-4xl font-bold mb-4">Our Journey</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto">
                From a local idea to a community health solution
              </p>
            </motion.div>

            <div className="relative">
              {/* Timeline Line */}
              <div className="absolute left-4 md:left-1/2 top-0 bottom-0 w-0.5 bg-gradient-to-b from-primary/20 via-primary to-primary/20"></div>

              <div className="space-y-12">
                {milestones.map((milestone, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.5, delay: index * 0.2 }}
                    className={`relative flex flex-col md:flex-row ${
                      index % 2 === 0 ? 'md:flex-row-reverse' : ''
                    } items-start gap-8`}
                  >
                    {/* Timeline Dot */}
                    <div className="absolute left-4 md:left-1/2 transform -translate-x-1/2 w-4 h-4 bg-primary rounded-full border-4 border-background z-10"></div>
                    
                    {/* Content */}
                    <div className={`ml-12 md:ml-0 md:w-1/2 ${
                      index % 2 === 0 ? 'md:pr-12' : 'md:pl-12'
                    }`}>
                      <Card className="p-6 hover:shadow-lg transition-all duration-300 border-2 hover:border-primary/50">
                        <Badge className="mb-3 bg-primary/10 text-primary border-primary/20">
                          {milestone.year}
                        </Badge>
                        <h3 className="text-xl font-bold mb-2">{milestone.title}</h3>
                        <p className="text-muted-foreground">{milestone.description}</p>
                      </Card>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Testimonial / Quote Section */}
        <section className="py-16 md:py-24 bg-primary/5 border-y border-primary/10">
          <div className="container mx-auto px-4 max-w-4xl">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              className="text-center"
            >
              <Quote className="h-12 w-12 text-primary/30 mx-auto mb-6" />
              <blockquote className="text-xl md:text-2xl italic text-foreground mb-6 leading-relaxed">
                "MediGuard has transformed how our community accesses preliminary health information. 
                It's like having a health assistant available 24/7."
              </blockquote>
              <div>
                <p className="font-semibold text-primary">— Dr. Sarah Ndifon</p>
                <p className="text-sm text-muted-foreground">Community Health Advisor, Bamenda</p>
              </div>
            </motion.div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-16 md:py-24">
          <div className="container mx-auto px-4 max-w-4xl">
            <motion.div 
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="bg-gradient-to-br from-primary via-primary/90 to-secondary rounded-3xl p-8 md:p-12 text-center text-white shadow-2xl"
            >
              <h2 className="text-2xl md:text-3xl lg:text-4xl font-bold mb-4">
                Join Us in Building Healthier Communities
              </h2>
              <p className="text-base md:text-lg text-white/90 mb-8 max-w-2xl mx-auto">
                Partner with us, share feedback, or support deployment in local clinics. 
                Your input helps make MediGuard more accurate and useful for everyone.
              </p>
              
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link to="/contact" className="w-full sm:w-auto">
                  <Button 
                    size="lg" 
                    variant="secondary" 
                    className="w-full sm:w-auto bg-white text-primary hover:bg-white/90 hover:scale-105 transition-all duration-300 shadow-lg text-base md:text-lg px-8 py-6"
                  >
                    <Mail className="mr-2 h-5 w-5" />
                    Support Us
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                </Link>
                
                <Link to="/symptom-checker" className="w-full sm:w-auto">
                  <Button 
                    size="lg" 
                    variant="outline" 
                    className="w-full sm:w-auto bg-transparent text-white border-white hover:bg-white/20 hover:scale-105 transition-all duration-300 text-base md:text-lg px-8 py-6"
                  >
                    <Activity className="mr-2 h-5 w-5" />
                    Try Symptom Checker
                  </Button>
                </Link>

                <Link to="/chat-ai" className="w-full sm:w-auto">
                  <Button 
                    size="lg" 
                    variant="outline" 
                    className="w-full sm:w-auto bg-transparent text-white border-white hover:bg-white/20 hover:scale-105 transition-all duration-300 text-base md:text-lg px-8 py-6"
                  >
                    <MessageCircle className="mr-2 h-5 w-5" />
                    Chat with AI
                  </Button>
                </Link>
              </div>

              {/* Trust Badges */}
              <div className="flex flex-wrap items-center justify-center gap-6 mt-8 text-white/80 text-sm">
                <span className="flex items-center gap-1">
                  <Shield className="h-4 w-4" /> Privacy Guaranteed
                </span>
                <span className="flex items-center gap-1">
                  <Award className="h-4 w-4" /> Community Trusted
                </span>
                <span className="flex items-center gap-1">
                  <Globe className="h-4 w-4" /> Free for All
                </span>
              </div>
            </motion.div>
          </div>
        </section>
      </div>
    </>
  );
};

export default About;