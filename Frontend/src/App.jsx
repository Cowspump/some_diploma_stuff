import React, { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
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
import TherapistDashboard from './pages/TherapistDashboard';

import "./styles/App.css";

function App() {
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userId] = useState("user_123");
  const [userRole, setUserRole] = useState(null);
  const [userData, setUserData] = useState(null);

  // Восстановление сессии при загрузке
  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      const user = JSON.parse(savedUser);
      setUserData(user);
      setUserRole(user.role);
      setIsLoggedIn(true);
    }
  }, []);

  const handleAuthSuccess = (authData) => {
    const user = {
      id: Math.random().toString(36).substr(2, 9),
      email: authData.email,
      role: authData.role || "worker",
      fullName: authData.fullName || "",
    };

    setUserData(user);
    setUserRole(user.role);
    setIsLoggedIn(true);

    // Сохранить в localStorage
    localStorage.setItem("user", JSON.stringify(user));

    setShowAuthModal(false);
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUserRole(null);
    setUserData(null);
    localStorage.removeItem("user");
  };

  // Если пользователь администратор или терапевт - переходим на их страницы
  if (isLoggedIn && userRole === "admin") {
    return (
      <Router>
        <Routes>
          <Route
            path="/admin"
            element={<AdminDashboard user={userData} onLogout={handleLogout} />}
          />
          <Route path="*" element={<Navigate to="/admin" replace />} />
        </Routes>
      </Router>
    );
  }

  if (isLoggedIn && userRole === "therapist") {
    return (
      <Router>
        <Routes>
          <Route
            path="/therapist"
            element={
              <TherapistDashboard user={userData} onLogout={handleLogout} />
            }
          />
          <Route path="*" element={<Navigate to="/therapist" replace />} />
        </Routes>
      </Router>
    );
  }

  // Главная страница для рабочих и неавторизованных пользователей
  return (
    <Router>
      <div className="app">
        <NavbarComponent
          onLoginClick={() => setShowAuthModal(true)}
          onSignUpClick={() => setShowAuthModal(true)}
          isLoggedIn={isLoggedIn}
          onLogoutClick={handleLogout}
          user={userData}
        />
        <AuthModal
          show={showAuthModal}
          handleClose={() => setShowAuthModal(false)}
          onAuthSuccess={handleAuthSuccess}
        />
        <Hero />
        <MaterialsSection />
        <TestSection />
        {isLoggedIn && <TestResultsHistory userId={userId} />}
        <AIAssistantSection />
        <MoodJournal isLoggedIn={isLoggedIn} />
        <BurnoutScale />
        <AnalyticsSection />
        <Footer />
      </div>
    </Router>
  );
}

export default App;
