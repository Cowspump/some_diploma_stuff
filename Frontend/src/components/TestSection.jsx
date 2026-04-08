import React, { useState } from "react";
import { Container, Row, Col, Button } from "react-bootstrap";
import { motion } from "framer-motion";
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
            <motion.div
              initial={{ opacity: 0, x: -40 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.7 }}
            >
              <h2 className="section-title mb-4">{t("test_title")}</h2>
              <p className="section-description mb-4">{t("test_desc")}</p>
              <ul className="test-benefits">
                {["test_benefit1", "test_benefit2", "test_benefit3", "test_benefit4"].map((key, i) => (
                  <motion.li
                    key={key}
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.4, delay: 0.2 + i * 0.1 }}
                  >
                    {t(key)}
                  </motion.li>
                ))}
              </ul>
              <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.98 }}>
                <Button className="btn-primary-custom mt-4" onClick={() => setShowTestModal(true)}>
                  {t("test_start")}
                </Button>
              </motion.div>
            </motion.div>
          </Col>
          <Col lg={6}>
            <motion.div
              className="test-image"
              initial={{ opacity: 0, x: 40 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.7, delay: 0.2 }}
            >
              <img src="/images/test-wellness.jpg" alt="Wellness Testing" />
            </motion.div>
          </Col>
        </Row>
      </Container>
      <TestModal show={showTestModal} onHide={() => setShowTestModal(false)} userId={user?.id || "guest"} />
    </section>
  );
};

export default TestSection;
