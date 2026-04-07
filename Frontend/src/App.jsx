import React, { useState } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { LanguageProvider } from "./contexts/LanguageContext";
import NavbarComponent from "./components/Navbar";
import AuthModal from "./components/AuthModal";
import Hero from "./components/Hero";
import MaterialsSection from "./components/MaterialsSection";
import TestSection from "./components/TestSection";
import TestResultsHistory from "./components/TestResultsHistory";
import AIAssistantSection from "./components/AIAssistantSection";
import MoodJournal from "./components/MoodJournal";
import BurnoutScale from "./components/BurnoutScale";
import AnalyticsSection from "./components/AnalyticsSection";
import Footer from "./components/Footer";
import AdminDashboard from "./pages/AdminDashboard";
import TherapistDashboard from "./pages/TherapistDashboard";

import "./styles/App.css";

function AppContent() {
  const { user, logout, loading } = useAuth();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authModalTab, setAuthModalTab] = useState("login");
  const [refreshKey, setRefreshKey] = useState(0);

  const handleLogout = () => {
    logout();
    setRefreshKey((k) => k + 1);
  };

  const handleLoginSuccess = () => {
    setShowAuthModal(false);
    setRefreshKey((k) => k + 1);
  };

  if (loading) {
    return (
      <div
        className="d-flex justify-content-center align-items-center"
        style={{ minHeight: "100vh" }}
      >
        <div className="spinner-border" role="status">
          <span className="visually-hidden">...</span>
        </div>
      </div>
    );
  }

  if (user && user.role === "admin") {
    return (
      <Routes>
        <Route
          path="/admin"
          element={<AdminDashboard user={user} onLogout={handleLogout} />}
        />
        <Route path="*" element={<Navigate to="/admin" replace />} />
      </Routes>
    );
  }

  if (user && user.role === "therapist") {
    return (
      <Routes>
        <Route
          path="/therapist"
          element={<TherapistDashboard user={user} onLogout={handleLogout} />}
        />
        <Route path="*" element={<Navigate to="/therapist" replace />} />
      </Routes>
    );
  }

  return (
    <div className="app">
      <NavbarComponent
        onLoginClick={() => {
          setAuthModalTab("login");
          setShowAuthModal(true);
        }}
        onSignUpClick={() => {
          setAuthModalTab("signup");
          setShowAuthModal(true);
        }}
        isLoggedIn={!!user}
        onLogoutClick={handleLogout}
        user={user}
      />
      <AuthModal
        show={showAuthModal}
        handleClose={() => setShowAuthModal(false)}
        initialTab={authModalTab}
        onLoginSuccess={handleLoginSuccess}
      />
      <Hero />
      <MaterialsSection />
      {(!user || user.role === "worker") && (
        <>
          <TestSection key={`test-${refreshKey}`} />
          {user && <TestResultsHistory key={`results-${refreshKey}`} userId={user.id} />}
          <AIAssistantSection />
          <MoodJournal key={`mood-${refreshKey}`} isLoggedIn={!!user} />
        </>
      )}
      <BurnoutScale key={`burnout-${refreshKey}`} />
      <AnalyticsSection key={`analytics-${refreshKey}`} />
      <Footer />
    </div>
  );
}

function App() {
  return (
    <Router>
      <LanguageProvider>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </LanguageProvider>
    </Router>
  );
}

export default App;
