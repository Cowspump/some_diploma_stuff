import React from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import '../styles/App.css';

const BurnoutScale = () => {
  const burnoutLevel = 35; // Mock value

  return (
    <section id="burnout" className="burnout-section py-5">
      <Container>
        <h2 className="section-title text-center mb-5">Burnout Risk Assessment</h2>
        <Row>
          <Col lg={8} className="mx-auto">
            <div className="burnout-card p-5 fade-in-animation">
              <div className="d-flex justify-content-between align-items-center mb-3">
                <span className="burnout-label">Your Burnout Risk Level</span>
                <span className="burnout-percentage fw-bold">{burnoutLevel}%</span>
              </div>

              <div className="burnout-progress-bar">
                <div
                  className="burnout-progress-fill"
                  style={{ width: `${burnoutLevel}%` }}
                ></div>
              </div>

              <p className="mt-4 mb-0 text-muted">
                <small>
                  Low burnout risk detected. Continue maintaining healthy habits and
                  regular self-care practices.
                </small>
              </p>
            </div>
          </Col>
        </Row>
      </Container>
    </section>
  );
};

export default BurnoutScale;