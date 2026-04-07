import React, { useState } from "react";
import { Container, Row, Col, Button } from "react-bootstrap";
import { useLanguage } from "../contexts/LanguageContext";
import AIChatModal from "./AIChatModal";
import "../styles/App.css";

const AIAssistantSection = () => {
  const [showChatModal, setShowChatModal] = useState(false);
  const { t } = useLanguage();

  return (
    <>
      <section id="ai-assistant" className="ai-section py-5">
        <Container>
          <Row className="align-items-center">
            <Col lg={6} className="order-lg-2 mb-4 mb-lg-0">
              <div className="fade-in-animation">
                <h2 className="section-title mb-4">{t("ai_title")}</h2>
                <p className="section-description mb-4">{t("ai_desc")}</p>
                <div className="ai-features">
                  <div className="feature-item">
                    <span className="feature-badge">{t("ai_available")}</span>
                    <p>{t("ai_available_desc")}</p>
                  </div>
                  <div className="feature-item">
                    <span className="feature-badge">{t("ai_smart")}</span>
                    <p>{t("ai_smart_desc")}</p>
                  </div>
                  <div className="feature-item">
                    <span className="feature-badge">{t("ai_safe")}</span>
                    <p>{t("ai_safe_desc")}</p>
                  </div>
                </div>
                <Button className="btn-primary-custom mt-4" onClick={() => setShowChatModal(true)}>
                  {t("ai_chat_now")}
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
      <AIChatModal show={showChatModal} onHide={() => setShowChatModal(false)} />
    </>
  );
};

export default AIAssistantSection;
