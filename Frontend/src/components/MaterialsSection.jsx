import React from "react";
import { Container, Row, Col, Card } from "react-bootstrap";
import { motion } from "framer-motion";
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
        <motion.h2
          className="section-title text-center mb-5"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
        >
          {t("materials_title")}
        </motion.h2>
        <Row className="g-4">
          {materials.map((m, index) => (
            <Col key={m.id} md={6} lg={3}>
              <motion.div
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                whileHover={{ y: -8 }}
              >
                <Card className="material-card h-100 border-0 shadow-sm">
                  <Card.Body className="d-flex flex-column">
                    <motion.div
                      className="material-icon mb-3"
                      whileHover={{ scale: 1.2, rotate: 10 }}
                      transition={{ type: "spring", stiffness: 300 }}
                    >
                      {m.icon}
                    </motion.div>
                    <Card.Title className="material-title">{t(m.titleKey)}</Card.Title>
                    <Card.Text className="material-text flex-grow-1">{t(m.descKey)}</Card.Text>
                    <a href="#" className="material-link mt-2">{t("materials_learn_more")}</a>
                  </Card.Body>
                </Card>
              </motion.div>
            </Col>
          ))}
        </Row>

        {/* Oil & Gas Banner */}
        <motion.div
          className="oil-gas-banner mt-5"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ duration: 0.6 }}
        >
          <img src="/images/hero-mental-health.jpg" alt="Mental Health Resources" />
          <div className="oil-gas-overlay">
            <h3>{t("mat_stress_title")}</h3>
            <p>{t("mat_stress_desc")}</p>
          </div>
        </motion.div>
      </Container>
    </section>
  );
};

export default MaterialsSection;
