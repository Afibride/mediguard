import React from 'react';
import { Route, Routes, BrowserRouter as Router } from 'react-router-dom';
import ScrollToTop from '@/components/ScrollToTop';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
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
import TermsPage from '@/pages/TermsPage';
import PrivacyPage from '@/pages/PrivacyPage';
import ProtectedRoute from '@/components/ProtectedRoute';
import { AuthProvider } from '@/components/AuthContext';
import MobileMenu from '@/components/MobileMenu'; // Kept for validation requirements
import About from '@/pages/About';

function App() {
  return (
    <Router>
      <AuthProvider>
        <ScrollToTop />
        <div className="flex flex-col min-h-screen">
          <Header />
          <main className="flex-1">
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
              
              <Route path="/symptom-checker" element={<SymptomChecker />} />
              <Route path="/prediction-results" element={<PredictionResults />} />
              <Route path="/chat-ai" element={<ChatAI />} />

              <Route path="/history" element={
                <ProtectedRoute>
                  <HistoryPage />
                </ProtectedRoute>
              } />
            </Routes>
          </main>
          <Footer />
        </div>
        <Toaster />
      </AuthProvider>
    </Router>
  );
}

export default App;
