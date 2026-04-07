import React from "react";
import { Container, Row, Col, Card } from "react-bootstrap";
import { useLanguage } from "../contexts/LanguageContext";
import "../styles/App.css";

const MaterialsSection = () => {
  const { t } = useLanguage();

  const materials = [
    { id: 1, titleKey: "mat_burnout_title", descKey: "mat_burnout_desc", icon: "🔥" },
    { id: 2, titleKey: "mat_mindfulness_title", descKey: "mat_mindfulness_desc", icon: "🧘" },
    { id: 3, titleKey: "mat_sleep_title", descKey: "mat_sleep_desc", icon: "😴" },
    { id: 4, titleKey: "mat_stress_title", descKey: "mat_stress_desc", icon: "🌿" },
  ];

  return (
    <section id="materials" className="materials-section py-5">
      <Container>
        <h2 className="section-title text-center mb-5">{t("materials_title")}</h2>
        <Row className="g-4">
          {materials.map((m) => (
            <Col key={m.id} md={6} lg={3} className="fade-in-animation">
              <Card className="material-card h-100 border-0 shadow-sm">
                <Card.Body className="d-flex flex-column">
                  <div className="material-icon mb-3">{m.icon}</div>
                  <Card.Title className="material-title">{t(m.titleKey)}</Card.Title>
                  <Card.Text className="material-text flex-grow-1">{t(m.descKey)}</Card.Text>
                  <a href="#" className="material-link mt-2">{t("materials_learn_more")}</a>
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
