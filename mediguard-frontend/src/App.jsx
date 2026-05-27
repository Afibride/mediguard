import React from 'react';
import { Route, Routes, BrowserRouter as Router, useLocation } from 'react-router-dom';
import ScrollToTop from '@/components/ScrollToTop';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import PWAInstallPrompt from '@/components/PWAInstallPrompt';
import { Toaster } from '@/components/ui/toaster';
import HomePage from '@/pages/HomePage';
import SymptomChecker from '@/pages/SymptomChecker';
import PredictionResults from '@/pages/PredictionResults';
import DiseaseLibrary from '@/pages/DiseaseLibrary';
import DiseaseDetail from '@/pages/DiseaseDetail';
import ChatAI from '@/pages/ChatAI';
import TrendsDashboard from '@/pages/TrendsDashboard';
import LoginPage from '@/pages/LoginPage';
import SignupPage from '@/pages/SignupPage';
import ForgotPasswordPage from '@/pages/ForgotPasswordPage';
import ResetPasswordPage from '@/pages/ResetPasswordPage';
import HistoryPage from '@/pages/HistoryPage';
import ProfilePage from '@/pages/ProfilePage';
import TermsPage from '@/pages/TermsPage';
import PrivacyPage from '@/pages/PrivacyPage';
import ProtectedRoute from '@/components/ProtectedRoute';
import { AuthProvider } from '@/components/AuthContext';
import { LanguageProvider } from '@/contexts/LanguageContext';
import MobileMenu from '@/components/MobileMenu'; // Kept for validation requirements
import About from '@/pages/About';
import Contact from '@/pages/Contact';
import NearbyFacilitiesPage from '@/pages/NearbyFacilitiesPage';

function AppLayout() {
  const location = useLocation();
  const isChatPage = location.pathname === '/chat-ai';

  return (
    <>
      <ScrollToTop />
      <div className={`flex flex-col min-h-screen ${isChatPage ? 'overflow-hidden' : ''}`}>
        <Header />
        <main className={`flex-1 ${isChatPage ? 'min-h-0' : ''}`}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/disease-library" element={<DiseaseLibrary />} />
            <Route path="/disease/:id" element={<DiseaseDetail />} />
            <Route path="/trends" element={<TrendsDashboard />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/terms" element={<TermsPage />} />
            <Route path="/privacy" element={<PrivacyPage />} />
            <Route path="/about" element={<About />} />
            <Route path="/support" element={<Contact />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/nearby-facilities" element={<NearbyFacilitiesPage />} />
            
            <Route path="/symptom-checker" element={<SymptomChecker />} />
            <Route path="/prediction-results" element={<PredictionResults />} />
            <Route path="/chat-ai" element={<ChatAI />} />

            <Route path="/profile" element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            } />

            <Route path="/history" element={
              <ProtectedRoute>
                <HistoryPage />
              </ProtectedRoute>
            } />
          </Routes>
        </main>
        {!isChatPage && <Footer />}
      </div>
      <Toaster />
      <PWAInstallPrompt />
    </>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <LanguageProvider>
          <AppLayout />
        </LanguageProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
