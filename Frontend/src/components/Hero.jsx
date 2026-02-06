import React from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import '../styles/App.css';

const Hero = () => {
  return (
    <section className="hero-section py-5" id="hero">
      <Container>
        <Row className="align-items-center min-vh-100">
          <Col lg={8} className="mx-auto text-center">
            <div className="fade-in-animation">
              <h1 className="hero-title mb-4">
                Your Journey to Better Well-Being Starts Here
              </h1>
              <p className="hero-subtitle mb-5">
                Discover personalized insights about your mental health, track your mood,
                and get AI-powered recommendations to improve your well-being.
              </p>
              <div className="hero-decoration"></div>
            </div>
          </Col>
        </Row>
      </Container>
    </section>
  );
};

export default Hero;