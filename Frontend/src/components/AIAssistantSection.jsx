import React, { useState } from "react";
import { Container, Row, Col, Button } from "react-bootstrap";
import { motion } from "framer-motion";
import { useLanguage } from "../contexts/LanguageContext";
import AIChatModal from "./AIChatModal";
import "../styles/App.css";

const AIAssistantSection = () => {
  const [showChatModal, setShowChatModal] = useState(false);
  const { t } = useLanguage();

  const features = [
    { badge: "ai_available", desc: "ai_available_desc" },
    { badge: "ai_smart", desc: "ai_smart_desc" },
    { badge: "ai_safe", desc: "ai_safe_desc" },
  ];

  return (
    <>
      <section id="ai-assistant" className="ai-section py-5">
        <Container>
          <Row className="align-items-center">
            <Col lg={6} className="order-lg-2 mb-4 mb-lg-0">
              <motion.div
                initial={{ opacity: 0, x: 40 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.7 }}
              >
                <h2 className="section-title mb-4">{t("ai_title")}</h2>
                <p className="section-description mb-4">{t("ai_desc")}</p>
                <div className="ai-features">
                  {features.map((f, i) => (
                    <motion.div
                      key={f.badge}
                      className="feature-item"
                      initial={{ opacity: 0, y: 20 }}
                      whileInView={{ opacity: 1, y: 0 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.4, delay: 0.2 + i * 0.1 }}
                      whileHover={{ x: 5 }}
                    >
                      <span className="feature-badge">{t(f.badge)}</span>
                      <p>{t(f.desc)}</p>
                    </motion.div>
                  ))}
                </div>
                <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.98 }}>
                  <Button className="btn-primary-custom mt-4" onClick={() => setShowChatModal(true)}>
                    {t("ai_chat_now")}
                  </Button>
                </motion.div>
              </motion.div>
            </Col>
            <Col lg={6} className="order-lg-1">
              <motion.div
                className="ai-image"
                initial={{ opacity: 0, x: -40 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.7, delay: 0.2 }}
              >
                <img src="/images/meditation.jpg" alt="AI Wellness Assistant" />
              </motion.div>
            </Col>
          </Row>
        </Container>
      </section>
      <AIChatModal show={showChatModal} onHide={() => setShowChatModal(false)} />
    </>
  );
};

export default AIAssistantSection;
