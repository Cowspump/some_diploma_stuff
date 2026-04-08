import React from "react";
import { Container, Row, Col } from "react-bootstrap";
import { motion } from "framer-motion";
import { useLanguage } from "../contexts/LanguageContext";
import "../styles/App.css";

const Hero = () => {
  const { t } = useLanguage();
  const heroTitle = t("hero_title");
  const heroTitleLines =
    heroTitle === "您的幸福之旅从这里开始"
      ? ["您的幸福之旅", "从这里开始"]
      : [heroTitle];
  return (
    <section className="hero-section py-5" id="hero">
      <img src="/images/hero-mental-health.jpg" alt="" className="hero-bg-image" />
      <Container>
        <Row className="align-items-center min-vh-100">
          <Col lg={6}>
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
            >
              <h1 className="hero-title">
                {heroTitleLines.map((line, idx) => (
                  <React.Fragment key={idx}>
                    {line}
                    {idx < heroTitleLines.length - 1 && <br />}
                  </React.Fragment>
                ))}
              </h1>
              <p className="hero-subtitle">{t("hero_subtitle")}</p>
              <div className="hero-decoration"></div>
              <div className="hero-stats">
                <div className="hero-stat">
                  <div className="hero-stat-value">24/7</div>
                  <div className="hero-stat-label">AI Support</div>
                </div>
                <div className="hero-stat">
                  <div className="hero-stat-value">100%</div>
                  <div className="hero-stat-label">{t("ai_safe")}</div>
                </div>
                <div className="hero-stat">
                  <div className="hero-stat-value">5+</div>
                  <div className="hero-stat-label">{t("therapist_tests")}</div>
                </div>
              </div>
            </motion.div>
          </Col>
          <Col lg={6}>
            <motion.div
              className="hero-image-container"
              initial={{ opacity: 0, x: 60 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
            >
              <img src="/images/therapy-session.jpg" alt="Mental Health Support" />
            </motion.div>
          </Col>
        </Row>
      </Container>
    </section>
  );
};

export default Hero;
