import React, { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
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

  const handleLogout = () => {
    logout();
    window.location.reload();
  };

  // Показываем индикатор загрузки пока проверяем сессию
  if (loading) {
    return (
      <div
        className="d-flex justify-content-center align-items-center"
        style={{ minHeight: "100vh" }}
      >
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Загрузка...</span>
        </div>
      </div>
    );
  }

  // Если пользователь администратор или терапевт - переходим на их страницы
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

  // Главная страница для рабочих и неавторизованных пользователей
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
      />
      <Hero />
      <MaterialsSection />
      {/* Показываем компоненты только для workers и неавторизованных */}
      {(!user || user.role === "worker") && (
        <>
          <TestSection />
          {user && <TestResultsHistory userId={user.id} />}
          <AIAssistantSection />
          <MoodJournal isLoggedIn={!!user} />
        </>
      )}
      <BurnoutScale />
      <AnalyticsSection />
      <Footer />
    </div>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}

export default App;
