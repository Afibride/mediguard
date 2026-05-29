import React from 'react';
import { Route, Routes, BrowserRouter as Router, useLocation, Navigate, Outlet } from 'react-router-dom';
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

// Admin pages
import { AdminAuthProvider, useAdminAuth } from '@/contexts/AdminAuthContext';
import AdminLogin from '@/pages/admin/AdminLogin';
import AdminLayout from '@/pages/admin/AdminLayout';
import AdminDashboard from '@/pages/admin/AdminDashboard';
import AdminUsers from '@/pages/admin/AdminUsers';
import AdminNewsletter from '@/pages/admin/AdminNewsletter';
import AdminTrends from '@/pages/admin/AdminTrends';
import AdminDiseases from '@/pages/admin/AdminDiseases';
import AdminMessages from '@/pages/admin/AdminMessages';
import AdminFeedback from '@/pages/admin/AdminFeedback';

// ── Admin auth guard ──────────────────────────────────────────────────────────
function AdminGuard() {
  const { admin, loading } = useAdminAuth();
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="w-7 h-7 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }
  return admin ? <Outlet /> : <Navigate to="/admin" replace />;
}

// ── Layout route: provides AdminAuthProvider to all /admin/* children ─────────
// This is the top-level admin wrapper. All /admin/* routes live inside here.
function AdminRoot() {
  return (
    <AdminAuthProvider>
      <Outlet />
    </AdminAuthProvider>
  );
}

// ── Main app wrapper (header + footer + toaster) ──────────────────────────────
function MainLayout() {
  const location = useLocation();
  const isChatPage = location.pathname === '/chat-ai';
  return (
    <>
      <ScrollToTop />
      <div className={`flex flex-col min-h-screen ${isChatPage ? 'overflow-hidden' : ''}`}>
        <Header />
        <main className={`flex-1 ${isChatPage ? 'min-h-0' : ''}`}>
          <Outlet />
        </main>
        {!isChatPage && <Footer />}
      </div>
      <Toaster />
      <PWAInstallPrompt />
    </>
  );
}

export default function App() {
  return (
    <Router>
      <Routes>

        {/* ════════════════════════════════════════════════════════════════
            ADMIN SECTION
            All routes share AdminAuthProvider through AdminRoot.
            /admin           → login page (index)
            /admin/dashboard → protected dashboard
            /admin/...       → other protected pages
        ════════════════════════════════════════════════════════════════ */}
        <Route path="/admin" element={<AdminRoot />}>
          {/* Index = login page */}
          <Route index element={<AdminLogin />} />

          {/* Protected pages behind AdminGuard */}
          <Route element={<AdminGuard />}>
            <Route element={<AdminLayout />}>
              <Route path="dashboard"  element={<AdminDashboard />} />
              <Route path="users"      element={<AdminUsers />} />
              <Route path="newsletter" element={<AdminNewsletter />} />
              <Route path="trends"     element={<AdminTrends />} />
              <Route path="diseases"   element={<AdminDiseases />} />
              <Route path="messages"   element={<AdminMessages />} />
              <Route path="feedback"   element={<AdminFeedback />} />
              {/* Default child redirect */}
              <Route index element={<Navigate to="dashboard" replace />} />
            </Route>
          </Route>
        </Route>

        {/* ════════════════════════════════════════════════════════════════
            MAIN APPLICATION
        ════════════════════════════════════════════════════════════════ */}
        <Route
          element={
            <AuthProvider>
              <LanguageProvider>
                <MainLayout />
              </LanguageProvider>
            </AuthProvider>
          }
        >
          <Route path="/"                   element={<HomePage />} />
          <Route path="/disease-library"    element={<DiseaseLibrary />} />
          <Route path="/disease/:id"        element={<DiseaseDetail />} />
          <Route path="/trends"             element={<TrendsDashboard />} />
          <Route path="/login"              element={<LoginPage />} />
          <Route path="/signup"             element={<SignupPage />} />
          <Route path="/forgot-password"    element={<ForgotPasswordPage />} />
          <Route path="/reset-password"     element={<ResetPasswordPage />} />
          <Route path="/terms"              element={<TermsPage />} />
          <Route path="/privacy"            element={<PrivacyPage />} />
          <Route path="/about"              element={<About />} />
          <Route path="/support"            element={<Contact />} />
          <Route path="/contact"            element={<Contact />} />
          <Route path="/nearby-facilities"  element={<NearbyFacilitiesPage />} />
          <Route path="/symptom-checker"    element={<SymptomChecker />} />
          <Route path="/prediction-results" element={<PredictionResults />} />
          <Route path="/chat-ai"            element={<ChatAI />} />
          <Route path="/profile"            element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
          <Route path="/history"            element={<ProtectedRoute><HistoryPage /></ProtectedRoute>} />
        </Route>

      </Routes>
    </Router>
  );
}
