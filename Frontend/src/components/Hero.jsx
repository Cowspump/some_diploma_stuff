import React from "react";
import { Container, Row, Col } from "react-bootstrap";
import { useLanguage } from "../contexts/LanguageContext";
import "../styles/App.css";

const Hero = () => {
  const { t } = useLanguage();
  return (
    <section className="hero-section py-5" id="hero">
      <Container>
        <Row className="align-items-center min-vh-100">
          <Col lg={8} className="mx-auto text-center">
            <div className="fade-in-animation">
              <h1 className="hero-title mb-4">{t("hero_title")}</h1>
              <p className="hero-subtitle mb-5">{t("hero_subtitle")}</p>
              <div className="hero-decoration"></div>
            </div>
          </Col>
        </Row>
      </Container>
    </section>
  );
};

export default Hero;
