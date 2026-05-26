import React from 'react';
import { Link } from 'react-router-dom';
import { Mail, MapPin } from 'lucide-react';

const Footer = () => {
  const quickLinks = [
    { name: 'Home', path: '/' },
    { name: 'About', path: '/about' },
    { name: 'Support', path: '/support' },
    { name: 'Symptom Checker', path: '/symptom-checker' },
    { name: 'Disease Library', path: '/disease-library' },
    { name: 'Nearby Facilities', path: '/nearby-facilities' },
    { name: 'Trends Dashboard', path: '/trends' },
    { name: 'MediGuard AI', path: '/chat-ai' },
  ];

  // Split links into two columns
  const midPoint = Math.ceil(quickLinks.length / 2);
  const firstColumnLinks = quickLinks.slice(0, midPoint);
  const secondColumnLinks = quickLinks.slice(midPoint);

  return (
    <footer className="bg-muted border-t mt-16">
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Branding - takes 4 columns */}
          <div className="md:col-span-4 space-y-3">
            <Link to="/" className="inline-block">
              <img 
                src="/mediguard.png" 
                alt="MediGuard Logo" 
                className="logo-sm h-10 w-auto"
              />
            </Link>
            <p className="text-sm text-muted-foreground">
              AI-driven health screening for Bamenda's community.
            </p>
          </div>

          {/* Quick Links - takes 4 columns with 2 internal columns */}
          <div className="md:col-span-4">
            <span className="text-sm font-semibold text-foreground mb-3 block">Quick Links</span>
            <div className="grid grid-cols-2 gap-x-4 gap-y-2">
              <ul className="space-y-2">
                {firstColumnLinks.map((link) => (
                  <li key={link.path}>
                    <Link
                      to={link.path}
                      className="text-sm text-muted-foreground hover:text-primary transition-colors"
                    >
                      {link.name}
                    </Link>
                  </li>
                ))}
              </ul>
              <ul className="space-y-2">
                {secondColumnLinks.map((link) => (
                  <li key={link.path}>
                    <Link
                      to={link.path}
                      className="text-sm text-muted-foreground hover:text-primary transition-colors"
                    >
                      {link.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Contact & Support - takes 4 columns */}
          <div className="md:col-span-4">
            <span className="text-sm font-semibold text-foreground mb-3 block">Contact & Support</span>
            <ul className="space-y-2">
              <li className="flex items-center space-x-2 text-sm text-muted-foreground">
                <MapPin className="h-4 w-4 text-primary flex-shrink-0" />
                <span>Bamenda, Cameroon</span>
              </li>
              <li className="flex items-center space-x-2 text-sm text-muted-foreground">
                <Mail className="h-4 w-4 text-primary flex-shrink-0" />
                <span>support@mediguard.info</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Disclaimer - more compact */}
        <div className="border-t mt-6 pt-6">
          <p className="text-xs text-muted-foreground text-center">
            ⚕️ AI-powered information only. Not medical advice. Always consult a healthcare professional.
          </p>
          <p className="text-xs text-muted-foreground text-center mt-1">
            © {new Date().getFullYear()} MediGuard Bamenda. Community care.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
