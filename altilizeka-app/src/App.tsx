import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores';
import { supabase } from './lib/supabase';
import { AuthGuard } from './components/AuthGuard';

// Pages
import { HomePage } from './pages/HomePage';
import { CouponDetailPage } from './pages/CouponDetailPage';
import { BuyStarsPage } from './pages/BuyStarsPage';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { ProfilePage } from './pages/ProfilePage';
import { StatsPage } from './pages/StatsPage';
import { WalletPage } from './pages/WalletPage';
import { MyCouponsPage } from './pages/MyCouponsPage';
import { PrivacyPolicyPage } from './pages/PrivacyPolicyPage';
import { TermsPage } from './pages/TermsPage';
import { OnboardingPage } from './pages/OnboardingPage';
import { FAQPage } from './pages/FAQPage';
import { AccountDeletionPage } from './pages/AccountDeletionPage';

import './index.css';

// Check if onboarding is complete
const isOnboardingComplete = () => localStorage.getItem('onboarding_complete') === 'true';

function App() {
  const fetchProfile = useAuthStore((s) => s.fetchProfile);

  useEffect(() => {
    // Initial fetch
    fetchProfile();

    // Listen for auth changes (login/logout/token refresh)
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, _session) => {
      if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') {
        fetchProfile();
      } else if (event === 'SIGNED_OUT') {
        useAuthStore.setState({ user: null, isAuthenticated: false });
        // Clear local storage if needed
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [fetchProfile]);

  return (
    <BrowserRouter>
      <Routes>
        {/* Onboarding - First time users */}
        <Route path="/onboarding" element={<OnboardingPage />} />

        {/* Public Auth Routes */}
        <Route
          path="/login"
          element={
            <AuthGuard requireAuth={false}>
              {isOnboardingComplete() ? <LoginPage /> : <Navigate to="/onboarding" replace />}
            </AuthGuard>
          }
        />
        <Route
          path="/signup"
          element={
            <AuthGuard requireAuth={false}>
              <SignupPage />
            </AuthGuard>
          }
        />

        {/* Protected Routes */}
        {/* Public Routes */}
        <Route path="/" element={<HomePage />} />
        <Route
          path="/coupon/:id"
          element={
            <AuthGuard>
              <CouponDetailPage />
            </AuthGuard>
          }
        />
        <Route
          path="/stars"
          element={
            <AuthGuard>
              <BuyStarsPage />
            </AuthGuard>
          }
        />
        <Route
          path="/wallet"
          element={
            <AuthGuard>
              <WalletPage />
            </AuthGuard>
          }
        />
        <Route
          path="/stats"
          element={
            <AuthGuard>
              <StatsPage />
            </AuthGuard>
          }
        />
        <Route
          path="/profile"
          element={
            <AuthGuard>
              <ProfilePage />
            </AuthGuard>
          }
        />
        <Route
          path="/my-coupons"
          element={
            <AuthGuard>
              <MyCouponsPage />
            </AuthGuard>
          }
        />

        {/* Placeholder Routes */}
        <Route path="/star-history" element={<AuthGuard><PlaceholderPage title="Yıldız Geçmişi" /></AuthGuard>} />

        {/* Legal & Support Pages */}
        <Route path="/privacy" element={<PrivacyPolicyPage />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/faq" element={<AuthGuard><FAQPage /></AuthGuard>} />
        <Route path="/account-deletion" element={<AuthGuard><AccountDeletionPage /></AuthGuard>} />
      </Routes>
    </BrowserRouter>
  );
}

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="min-h-screen bg-background-dark flex flex-col items-center justify-center">
      <span className="material-symbols-outlined text-6xl text-gray-600 mb-4">construction</span>
      <h1 className="text-2xl font-bold text-white mb-2">{title}</h1>
      <p className="text-gray-500">Yakında...</p>
    </div>
  );
}

export default App;
