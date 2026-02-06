import React from 'react';
import { Container, Row, Col, Button } from 'react-bootstrap';
import '../styles/App.css';

const TestSection = () => {
  const handleStartTest = () => {
    alert('Well-being test is starting...');
  };

  return (
    <section id="test" className="test-section py-5">
      <Container>
        <Row className="align-items-center">
          <Col lg={6} className="mb-4 mb-lg-0">
            <div className="fade-in-animation">
              <h2 className="section-title mb-4">Well-Being Test</h2>
              <p className="section-description mb-4">
                Take our comprehensive well-being assessment to understand your current
                mental health status. Get personalized insights based on your answers.
              </p>
              <ul className="test-benefits">
                <li>✓ Quick and easy assessment</li>
                <li>✓ Personalized insights</li>
                <li>✓ Track progress over time</li>
                <li>✓ Science-backed questions</li>
              </ul>
              <Button
                className="btn-primary-custom mt-4"
                onClick={handleStartTest}
              >
                Start the Test →
              </Button>
            </div>
          </Col>
          <Col lg={6}>
            <div className="test-illustration">
              <div className="illustration-circle"></div>
            </div>
          </Col>
        </Row>
      </Container>
    </section>
  );
};

export default TestSection;