
import React, { useState } from 'react';
import { Container, Row, Col, Button } from 'react-bootstrap';
import AIChatModal from './AIChatModal';
import '../styles/App.css';

const AIAssistantSection = () => {
  const [showChatModal, setShowChatModal] = useState(false);

  // Пример данных (в реальном приложении они будут из БД)
  const journalHistory = [
    {
      id: 1,
      date: new Date('2026-02-01'),
      mood: 'neutral',
      content: 'Продуктивный день, но чувствую усталость к концу дня.',
    },
    {
      id: 2,
      date: new Date('2026-02-02'),
      mood: 'happy',
      content: 'Отличный день! Много положительных моментов.',
    },
    {
      id: 3,
      date: new Date('2026-02-03'),
      mood: 'anxious',
      content: 'Беспокойство из-за предстоящих задач.',
    },
  ];

  const testResults = [
    { id: 1, name: 'Стресс-тест', score: 65, date: new Date('2026-02-01') },
    { id: 2, name: 'Выгорание', score: 55, date: new Date('2026-02-03') },
    { id: 3, name: 'Благополучие', score: 72, date: new Date('2026-02-05') },
  ];

  const handleStartChat = () => {
    setShowChatModal(true);
  };

  return (
    <>
      <section id="ai-assistant" className="ai-section py-5">
        <Container>
          <Row className="align-items-center">
            <Col lg={6} className="order-lg-2 mb-4 mb-lg-0">
              <div className="fade-in-animation">
                <h2 className="section-title mb-4">AI-Powered Assistant</h2>
                <p className="section-description mb-4">
                  Chat with our intelligent assistant trained to provide emotional support
                  and personalized recommendations for your well-being journey.
                </p>
                <div className="ai-features">
                  <div className="feature-item">
                    <span className="feature-badge">24/7</span>
                    <p>Available anytime you need support</p>
                  </div>
                  <div className="feature-item">
                    <span className="feature-badge">Smart</span>
                    <p>Learns from your patterns and preferences</p>
                  </div>
                  <div className="feature-item">
                    <span className="feature-badge">Safe</span>
                    <p>Confidential and secure conversations</p>
                  </div>
                </div>
                <Button
                  className="btn-primary-custom mt-4"
                  onClick={handleStartChat}
                >
                  Chat Now →
                </Button>
              </div>
            </Col>
            <Col lg={6} className="order-lg-1">
              <div className="ai-illustration">
                <div className="illustration-circle ai-circle"></div>
              </div>
            </Col>
          </Row>
        </Container>
      </section>

      <AIChatModal
        show={showChatModal}
        onHide={() => setShowChatModal(false)}
        journalHistory={journalHistory}
        testResults={testResults}
      />
    </>
  );
};

export default AIAssistantSection;