import React from 'react';
import { Link } from 'react-router-dom';
import { Mail, Phone, MapPin } from 'lucide-react';

const Footer = () => {
  const quickLinks = [
    { name: 'Home', path: '/' },
    { name: 'About', path: '/about' },
    { name: 'Symptom Checker', path: '/symptom-checker' },
    { name: 'Disease Library', path: '/disease-library' },
    { name: 'Trends Dashboard', path: '/trends' },
    { name: 'MediGuard AI', path: '/chat-ai' },
  ];

  return (
    <footer className="bg-muted border-t mt-16">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Branding */}
          <div className="space-y-4">
            <Link to="/" className="inline-block">
              <img 
                src="/public/mediguard.png" 
                alt="MediGuard Logo" 
                className="logo-sm"
              />
            </Link>
            <p className="text-sm text-muted-foreground">
              AI-driven health screening for Bamenda's community.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <span className="text-sm font-semibold text-foreground mb-4 block">Quick Links</span>
            <ul className="space-y-2">
              {quickLinks.map((link) => (
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

          {/* Contact & Support */}
          <div>
            <span className="text-sm font-semibold text-foreground mb-4 block">Contact & Support</span>
            <ul className="space-y-3">
              <li className="flex items-center space-x-2 text-sm text-muted-foreground">
                <MapPin className="h-4 w-4 text-primary" />
                <span>Bamenda, Cameroon</span>
              </li>
              <li className="flex items-center space-x-2 text-sm text-muted-foreground">
                <Phone className="h-4 w-4 text-primary" />
                <span>+237 654 710 698</span>
              </li>
              <li className="flex items-center space-x-2 text-sm text-muted-foreground">
                <Mail className="h-4 w-4 text-primary" />
                <span>support@mediguard.cm</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="border-t mt-8 pt-8">
          <p className="text-xs text-muted-foreground text-center">
            ⚕️ AI-powered information only. Not medical advice. Always consult a healthcare professional.
          </p>
          <p className="text-xs text-muted-foreground text-center mt-2">
            © {new Date().getFullYear()} MediGuard Bamenda. Community care.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;