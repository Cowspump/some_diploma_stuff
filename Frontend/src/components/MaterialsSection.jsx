import React from 'react';
import { Container, Row, Col, Card } from 'react-bootstrap';
import '../styles/App.css';

const MaterialsSection = () => {
  const materials = [
    {
      id: 1,
      title: 'Understanding Burnout',
      description: 'Learn the signs of burnout and effective strategies to prevent it.',
      icon: '🔥',
    },
    {
      id: 2,
      title: 'Mindfulness Guide',
      description: 'Simple techniques to practice mindfulness in your daily routine.',
      icon: '🧘',
    },
    {
      id: 3,
      title: 'Sleep Optimization',
      description: 'Evidence-based tips for better sleep quality and restful nights.',
      icon: '😴',
    },
    {
      id: 4,
      title: 'Stress Management',
      description: 'Proven methods to manage stress and build resilience.',
      icon: '🌿',
    },
  ];

  return (
    <section id="materials" className="materials-section py-5">
      <Container>
        <h2 className="section-title text-center mb-5">Useful Materials</h2>
        <Row className="g-4">
          {materials.map((material) => (
            <Col key={material.id} md={6} lg={3} className="fade-in-animation">
              <Card className="material-card h-100 border-0 shadow-sm">
                <Card.Body className="d-flex flex-column">
                  <div className="material-icon mb-3">{material.icon}</div>
                  <Card.Title className="material-title">{material.title}</Card.Title>
                  <Card.Text className="material-text flex-grow-1">
                    {material.description}
                  </Card.Text>
                  <a href="#" className="material-link mt-2">
                    Learn more →
                  </a>
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>
      </Container>
    </section>
  );
};

export default MaterialsSection;