import React, { useState } from 'react';
import { Helmet } from 'react-helmet';
import { motion } from 'framer-motion';
import { 
  Mail, Send, MessageCircle, 
  CheckCircle, AlertCircle, Facebook, Twitter,
  Instagram, Linkedin, Shield, Users, Heart, Globe,
  HelpCircle, Bot, Phone, ExternalLink
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { Link } from 'react-router-dom';

const Contact = () => {
  const { toast } = useToast();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  });
  const [sending, setSending] = useState(false);
  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    if (!formData.subject.trim()) {
      newErrors.subject = 'Subject is required';
    }
    
    if (!formData.message.trim()) {
      newErrors.message = 'Message is required';
    } else if (formData.message.length < 20) {
      newErrors.message = 'Message should be at least 20 characters';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error for this field when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      toast({
        variant: "destructive",
        title: "Validation Error",
        description: "Please check all fields and try again.",
      });
      return;
    }
    
    setSending(true);

    // Simulate sending (replace with actual API call)
    setTimeout(() => {
      // In production, replace with actual email service
      const subject = encodeURIComponent(`MediGuard Support: ${formData.subject} - ${formData.name}`);
      const body = encodeURIComponent(
        `Name: ${formData.name}\n` +
        `Email: ${formData.email}\n` +
        `Subject: ${formData.subject}\n\n` +
        `${formData.message}\n\n` +
        `---\n` +
        `Sent from MediGuard Support Form`
      );
      
      // Open default email client
      window.location.href = `mailto:support@mediguard.cm?subject=${subject}&body=${body}`;
      
      toast({
        title: "Message Ready!",
        description: "Your default email client will open to send your message.",
        duration: 5000,
      });
      
      setFormData({ name: '', email: '', subject: '', message: '' });
      setSending(false);
    }, 1000);
  };

  const supportOptions = [
    {
      icon: Mail,
      title: "Email Support",
      description: "Get help via email",
      details: ["support@mediguard.cm"],
      action: "Send Email",
      href: "mailto:support@mediguard.cm",
      bgColor: "bg-blue-100 dark:bg-blue-900/20",
      iconColor: "text-blue-600 dark:text-blue-400"
    },
    {
      icon: Bot,
      title: "AI Chat Assistant",
      description: "Instant answers 24/7",
      details: ["Get immediate help", "No waiting time"],
      action: "Chat Now",
      href: "/chat-ai",
      bgColor: "bg-purple-100 dark:bg-purple-900/20",
      iconColor: "text-purple-600 dark:text-purple-400"
    },
    {
      icon: HelpCircle,
      title: "FAQ & Guides",
      description: "Find answers quickly",
      details: ["Common questions", "User guides"],
      action: "Browse FAQs",
      href: "/faq",
      bgColor: "bg-green-100 dark:bg-green-900/20",
      iconColor: "text-green-600 dark:text-green-400"
    },
    {
      icon: Phone,
      title: "Emergency",
      description: "For urgent medical needs",
      details: ["Emergency: +237 654 710 698"],
      action: "Call Now",
      href: "tel:+237654710698",
      bgColor: "bg-red-100 dark:bg-red-900/20",
      iconColor: "text-red-600 dark:text-red-400"
    }
  ];

  const socialLinks = [
    { icon: Facebook, href: "https://facebook.com/mediguard", label: "Facebook", color: "hover:bg-blue-600" },
    { icon: Twitter, href: "https://twitter.com/mediguard", label: "Twitter", color: "hover:bg-sky-500" },
    { icon: Instagram, href: "https://instagram.com/mediguard", label: "Instagram", color: "hover:bg-pink-600" },
    { icon: Linkedin, href: "https://linkedin.com/company/mediguard", label: "LinkedIn", color: "hover:bg-blue-700" }
  ];

  const faqs = [
    {
      question: "How do I use the symptom checker?",
      answer: "Simply select your symptoms from the list, add any optional details like duration and severity, then click 'Get Diagnosis' for instant results."
    },
    {
      question: "Is my information kept private?",
      answer: "Absolutely. We respect your privacy and never share your personal information with third parties. All communications are encrypted and confidential."
    },
    {
      question: "How accurate is the AI diagnosis?",
      answer: "Our AI provides preliminary guidance based on symptom matching. While highly informative, it should not replace professional medical advice."
    },
    {
      question: "Can I save my diagnosis history?",
      answer: "Yes! Create a free account to save your symptom checks and access them anytime from your history."
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
        <title>Support — MediGuard Bamenda | Get Help & Assistance</title>
        <meta name="description" content="Get support for MediGuard Bamenda. Contact our team for help with symptom checking, account issues, or general inquiries." />
        <meta property="og:title" content="MediGuard Bamenda Support - We're Here to Help" />
        <meta property="og:description" content="Get assistance with our AI-powered health screening tool. Multiple support channels available." />
      </Helmet>

      <div className="min-h-screen bg-gradient-to-b from-background via-background to-muted/30">
        {/* Hero Section */}
        <section className="relative py-20 overflow-hidden">
          {/* Background Pattern */}
          <div className="absolute inset-0 -z-10">
            <div className="absolute top-0 left-0 w-full h-96 bg-gradient-to-br from-primary/5 via-transparent to-transparent"></div>
            <div className="absolute bottom-0 right-0 w-full h-96 bg-gradient-to-tl from-secondary/5 via-transparent to-transparent"></div>
          </div>

          <div className="container mx-auto px-4 max-w-6xl">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="text-center mb-12"
            >
              <Badge variant="outline" className="mb-4 px-4 py-1 text-sm">
                <MessageCircle className="h-3 w-3 mr-1 inline" /> We're Here to Help
              </Badge>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 bg-gradient-to-r from-primary via-primary/80 to-secondary bg-clip-text text-transparent">
                How Can We Support You?
              </h1>
              <p className="text-lg md:text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
                Choose the best way to get help — from instant AI assistance to direct email support.
              </p>
            </motion.div>

            {/* Support Options Cards */}
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-16"
            >
              {supportOptions.map((option, index) => (
                <motion.div key={index} variants={itemVariants}>
                  <Card className="h-full hover:shadow-xl transition-all duration-300 border-2 hover:border-primary/50 bg-card/50 backdrop-blur-sm group">
                    <CardContent className="p-6 flex flex-col h-full">
                      <div className={`w-14 h-14 rounded-xl ${option.bgColor} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                        <option.icon className={`h-7 w-7 ${option.iconColor}`} />
                      </div>
                      <h3 className="text-lg font-semibold mb-2">{option.title}</h3>
                      <p className="text-sm text-muted-foreground mb-3">{option.description}</p>
                      {option.details.map((detail, i) => (
                        <p key={i} className="text-xs text-muted-foreground">{detail}</p>
                      ))}
                      <div className="mt-4 pt-4 border-t border-border">
                        {option.href.startsWith('http') || option.href.startsWith('mailto') || option.href.startsWith('tel') ? (
                          <a 
                            href={option.href}
                            className="text-primary hover:text-primary/80 text-sm font-medium flex items-center gap-1 transition-colors"
                            target={option.href.startsWith('http') ? "_blank" : undefined}
                            rel={option.href.startsWith('http') ? "noopener noreferrer" : undefined}
                          >
                            {option.action}
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        ) : (
                          <Link 
                            to={option.href}
                            className="text-primary hover:text-primary/80 text-sm font-medium flex items-center gap-1 transition-colors"
                          >
                            {option.action}
                            <ExternalLink className="h-3 w-3" />
                          </Link>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* Main Support Form Section */}
        <section className="py-12 md:py-20 bg-muted/30 border-y border-border">
          <div className="container mx-auto px-4 max-w-6xl">
            <div className="grid lg:grid-cols-2 gap-12 items-start">
              {/* Left Column - Form */}
              <motion.div
                initial={{ opacity: 0, x: -30 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6 }}
              >
                <div className="mb-8">
                  <h2 className="text-3xl font-bold mb-4">Send Us a Message</h2>
                  <p className="text-muted-foreground">
                    Fill out the form below and our support team will get back to you within 24 hours.
                  </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid sm:grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="name" className="block text-sm font-medium mb-2">
                        Your Name <span className="text-destructive">*</span>
                      </label>
                      <Input
                        id="name"
                        name="name"
                        type="text"
                        placeholder="John Doe"
                        value={formData.name}
                        onChange={handleChange}
                        className={`h-12 ${errors.name ? 'border-destructive focus-visible:ring-destructive' : ''}`}
                      />
                      {errors.name && (
                        <p className="text-sm text-destructive mt-1 flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" /> {errors.name}
                        </p>
                      )}
                    </div>

                    <div>
                      <label htmlFor="email" className="block text-sm font-medium mb-2">
                        Email Address <span className="text-destructive">*</span>
                      </label>
                      <Input
                        id="email"
                        name="email"
                        type="email"
                        placeholder="john@example.com"
                        value={formData.email}
                        onChange={handleChange}
                        className={`h-12 ${errors.email ? 'border-destructive focus-visible:ring-destructive' : ''}`}
                      />
                      {errors.email && (
                        <p className="text-sm text-destructive mt-1 flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" /> {errors.email}
                        </p>
                      )}
                    </div>
                  </div>

                  <div>
                    <label htmlFor="subject" className="block text-sm font-medium mb-2">
                      Subject <span className="text-destructive">*</span>
                    </label>
                    <Input
                      id="subject"
                      name="subject"
                      type="text"
                      placeholder="What is this regarding?"
                      value={formData.subject}
                      onChange={handleChange}
                      className={`h-12 ${errors.subject ? 'border-destructive focus-visible:ring-destructive' : ''}`}
                    />
                    {errors.subject && (
                      <p className="text-sm text-destructive mt-1 flex items-center gap-1">
                        <AlertCircle className="h-3 w-3" /> {errors.subject}
                      </p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="message" className="block text-sm font-medium mb-2">
                      Message <span className="text-destructive">*</span>
                    </label>
                    <Textarea
                      id="message"
                      name="message"
                      placeholder="Please describe how we can help you..."
                      value={formData.message}
                      onChange={handleChange}
                      rows={6}
                      className={`resize-none ${errors.message ? 'border-destructive focus-visible:ring-destructive' : ''}`}
                    />
                    {errors.message && (
                      <p className="text-sm text-destructive mt-1 flex items-center gap-1">
                        <AlertCircle className="h-3 w-3" /> {errors.message}
                      </p>
                    )}
                    <p className="text-xs text-muted-foreground mt-2">
                      {formData.message.length}/500 characters minimum
                    </p>
                  </div>

                  <div className="flex items-center gap-4">
                    <Button 
                      type="submit" 
                      disabled={sending}
                      size="lg"
                      className="min-w-[160px] h-12 bg-gradient-to-r from-primary to-secondary hover:from-primary/90 hover:to-secondary/90 text-white shadow-lg hover:shadow-xl transition-all duration-300"
                    >
                      {sending ? (
                        <>
                          <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-2" />
                          Sending...
                        </>
                      ) : (
                        <>
                          <Send className="mr-2 h-4 w-4" />
                          Send Message
                        </>
                      )}
                    </Button>
                    <p className="text-xs text-muted-foreground">
                      <Shield className="h-3 w-3 inline mr-1" />
                      Your data is encrypted
                    </p>
                  </div>
                </form>
              </motion.div>

              {/* Right Column - FAQ & Support Info */}
              <motion.div
                initial={{ opacity: 0, x: 30 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6 }}
                className="space-y-8"
              >
                {/* Quick Support Card */}
                <Card className="p-8 bg-gradient-to-br from-primary/5 to-secondary/5 border-2 border-primary/20">
                  <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                    <Bot className="h-5 w-5 text-primary" />
                    Try Our AI Assistant First
                  </h3>
                  <p className="text-muted-foreground mb-6">
                    Get instant answers to common questions without waiting for email response.
                  </p>
                  <div className="flex flex-col sm:flex-row gap-4">
                    <Link to="/chat-ai" className="flex-1">
                      <Button variant="default" className="w-full">
                        <MessageCircle className="mr-2 h-4 w-4" />
                        Chat with AI Now
                      </Button>
                    </Link>
                    <a href="mailto:support@mediguard.cm" className="flex-1">
                      <Button variant="outline" className="w-full">
                        <Mail className="mr-2 h-4 w-4" />
                        Email Support
                      </Button>
                    </a>
                  </div>
                </Card>

                {/* FAQ Section */}
                <Card className="p-8">
                  <h3 className="text-xl font-semibold mb-6">Frequently Asked Questions</h3>
                  <div className="space-y-6">
                    {faqs.map((faq, index) => (
                      <div key={index} className="border-b border-border last:border-0 pb-6 last:pb-0">
                        <h4 className="font-medium mb-2 flex items-start gap-2">
                          <span className="text-primary mt-1">•</span>
                          <span>{faq.question}</span>
                        </h4>
                        <p className="text-sm text-muted-foreground pl-4">{faq.answer}</p>
                      </div>
                    ))}
                  </div>
                  <div className="mt-6 pt-4 border-t border-border">
                    <Link to="/faq" className="text-primary hover:text-primary/80 text-sm font-medium flex items-center gap-1">
                      View all FAQs <ExternalLink className="h-3 w-3" />
                    </Link>
                  </div>
                </Card>

                {/* Social Links */}
                <Card className="p-8">
                  <h3 className="text-xl font-semibold mb-4">Connect With Us</h3>
                  <p className="text-muted-foreground mb-6">
                    Follow us on social media for updates, health tips, and community news.
                  </p>
                  <div className="flex gap-4">
                    {socialLinks.map((social, index) => (
                      <a
                        key={index}
                        href={social.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`w-12 h-12 rounded-full bg-muted flex items-center justify-center hover:text-white transition-all duration-300 ${social.color} hover:scale-110`}
                        aria-label={social.label}
                      >
                        <social.icon className="h-5 w-5" />
                      </a>
                    ))}
                  </div>
                </Card>
              </motion.div>
            </div>
          </div>
        </section>

        {/* Trust Badges */}
        <section className="py-16">
          <div className="container mx-auto px-4 max-w-4xl">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="flex flex-wrap items-center justify-center gap-8 p-8 bg-muted/30 rounded-2xl"
            >
              <div className="flex items-center gap-2 text-sm">
                <Shield className="h-5 w-5 text-primary" />
                <span>Privacy Guaranteed</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span>24/7 AI Support</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Users className="h-5 w-5 text-blue-500" />
                <span>Community First</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Heart className="h-5 w-5 text-red-500" />
                <span>Free for All</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Globe className="h-5 w-5 text-purple-500" />
                <span>Made in Cameroon</span>
              </div>
            </motion.div>
          </div>
        </section>
      </div>
    </>
  );
};

export default Contact;