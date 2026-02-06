import React, { useState } from 'react';
import NavbarComponent from './components/Navbar';
import Hero from './components/Hero';
import MaterialsSection from './components/MaterialsSection';
import TestSection from './components/TestSection';
import AIAssistantSection from './components/AIAssistantSection';
import MoodJournal from './components/MoodJournal';
import BurnoutScale from './components/BurnoutScale';
import AnalyticsSection from './components/AnalyticsSection';
import Footer from './components/Footer';
import './styles/App.css';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLoginClick = () => {
    setIsLoggedIn(true);
    alert('Logged in successfully!');
  };

  const handleSignUpClick = () => {
    setIsLoggedIn(true);
    alert('Account created successfully!');
  };

  const handleLogoutClick = () => {
    setIsLoggedIn(false);
    alert('Logged out successfully!');
  };

  return (
    <div className="app">
      <NavbarComponent
        onLoginClick={handleLoginClick}
        onSignUpClick={handleSignUpClick}
        isLoggedIn={isLoggedIn}
        onLogoutClick={handleLogoutClick}
      />
      <Hero />
      <MaterialsSection />
      <TestSection />
      <AIAssistantSection />
      <MoodJournal isLoggedIn={isLoggedIn} />
      <BurnoutScale />
      <AnalyticsSection />
      <Footer />
    </div>
  );
}

export default App;