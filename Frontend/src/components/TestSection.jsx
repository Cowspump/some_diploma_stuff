import React, { useState } from "react";
import { Container, Row, Col, Button } from "react-bootstrap";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import TestModal from "./TestModal";
import "../styles/App.css";

const TestSection = () => {
  const [showTestModal, setShowTestModal] = useState(false);
  const { user } = useAuth();
  const { t } = useLanguage();

  return (
    <section id="test" className="test-section py-5">
      <Container>
        <Row className="align-items-center">
          <Col lg={6} className="mb-4 mb-lg-0">
            <div className="fade-in-animation">
              <h2 className="section-title mb-4">{t("test_title")}</h2>
              <p className="section-description mb-4">{t("test_desc")}</p>
              <ul className="test-benefits">
                <li>✓ {t("test_benefit1")}</li>
                <li>✓ {t("test_benefit2")}</li>
                <li>✓ {t("test_benefit3")}</li>
                <li>✓ {t("test_benefit4")}</li>
              </ul>
              <Button className="btn-primary-custom mt-4" onClick={() => setShowTestModal(true)}>
                {t("test_start")}
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
      <TestModal show={showTestModal} onHide={() => setShowTestModal(false)} userId={user?.id || "guest"} />
    </section>
  );
};

export default TestSection;
