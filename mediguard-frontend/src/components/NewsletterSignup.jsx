import React, { useState } from 'react';
import { Mail, Send, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { subscribeNewsletter } from '@/services/api';

const NewsletterSignup = ({ compact = false }) => {
  const { toast } = useToast();
  const [formData, setFormData] = useState({ name: '', email: '' });
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!/\S+@\S+\.\S+/.test(formData.email)) {
      toast({
        variant: 'destructive',
        title: 'Check your email',
        description: 'Enter a valid email address to subscribe.',
      });
      return;
    }

    setSubmitting(true);
    try {
      const response = await subscribeNewsletter({
        name: formData.name.trim() || 'Friend',
        email: formData.email.trim(),
      });
      toast({
        title: 'Subscribed',
        description: response.data?.message || 'You are now subscribed to MediGuard updates.',
      });
      setFormData({ name: '', email: '' });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Subscription failed',
        description: error.message || 'Please try again in a moment.',
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className={compact ? '' : 'py-12 sm:py-20 bg-background'}>
      <div className={compact ? '' : 'container mx-auto px-4'}>
        <div className="overflow-hidden rounded-lg border bg-card shadow-sm">
          <div className="grid gap-0 lg:grid-cols-[1fr_420px]">
            <div className="p-6 sm:p-8 lg:p-10">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-sm font-semibold text-primary">
                <Mail className="h-4 w-4" />
                Health newsletter
              </div>
              <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
                Get local health alerts and monthly prevention tips
              </h2>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base">
                Subscribe for MediGuard updates on outbreak signals, seasonal health reminders, and practical care guidance for the Bamenda community.
              </p>
              <div className="mt-5 flex flex-wrap gap-3 text-xs text-muted-foreground sm:text-sm">
                <span className="inline-flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-primary" />
                  No spam
                </span>
                <span className="inline-flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-primary" />
                  Unsubscribe anytime
                </span>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="border-t bg-muted/35 p-6 sm:p-8 lg:border-l lg:border-t-0">
              <div className="space-y-4">
                <div>
                  <label htmlFor="newsletter-name" className="mb-2 block text-sm font-medium">
                    Name
                  </label>
                  <Input
                    id="newsletter-name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    placeholder="Your name"
                    autoComplete="name"
                    className="h-11 bg-background"
                  />
                </div>
                <div>
                  <label htmlFor="newsletter-email" className="mb-2 block text-sm font-medium">
                    Email address
                  </label>
                  <Input
                    id="newsletter-email"
                    name="email"
                    type="email"
                    required
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="you@example.com"
                    autoComplete="email"
                    className="h-11 bg-background"
                  />
                </div>
                <Button type="submit" disabled={submitting} className="h-11 w-full">
                  {submitting ? (
                    <>
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                      Subscribing
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4" />
                      Subscribe
                    </>
                  )}
                </Button>
              </div>
              <p className="mt-4 text-xs leading-5 text-muted-foreground">
                We use your email only for MediGuard health updates and alerts.
              </p>
            </form>
          </div>
        </div>
      </div>
    </section>
  );
};

export default NewsletterSignup;
