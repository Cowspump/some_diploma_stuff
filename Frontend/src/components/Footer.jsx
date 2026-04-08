import React from "react";
import { Container, Row, Col } from "react-bootstrap";
import { motion } from "framer-motion";
import { useLanguage } from "../contexts/LanguageContext";
import "../styles/App.css";

const Footer = () => {
  const { t } = useLanguage();
  const currentYear = new Date().getFullYear();

  return (
    <motion.footer
      className="footer-section py-5 mt-5"
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6 }}
    >
      <Container>
        <Row className="g-4 mb-5">
          <Col md={6} lg={3}>
            <h6 className="footer-title mb-3">{t("footer_about")}</h6>
            <ul className="footer-links">
              <li><a href="#" className="footer-link">{t("footer_about_us")}</a></li>
              <li><a href="#" className="footer-link">{t("footer_mission")}</a></li>
              <li><a href="#" className="footer-link">{t("footer_research")}</a></li>
            </ul>
          </Col>
          <Col md={6} lg={3}>
            <h6 className="footer-title mb-3">{t("footer_resources")}</h6>
            <ul className="footer-links">
              <li><a href="#" className="footer-link">{t("footer_blog")}</a></li>
              <li><a href="#" className="footer-link">{t("footer_guides")}</a></li>
              <li><a href="#" className="footer-link">{t("footer_faq")}</a></li>
            </ul>
          </Col>
          <Col md={6} lg={3}>
            <h6 className="footer-title mb-3">{t("footer_legal")}</h6>
            <ul className="footer-links">
              <li><a href="#" className="footer-link">{t("footer_privacy")}</a></li>
              <li><a href="#" className="footer-link">{t("footer_terms")}</a></li>
              <li><a href="#" className="footer-link">{t("footer_contact")}</a></li>
            </ul>
          </Col>
          <Col md={6} lg={3}>
            <h6 className="footer-title mb-3">{t("footer_follow")}</h6>
            <div className="social-links">
              <a href="#" className="social-link">Twitter</a>
              <a href="#" className="social-link">Instagram</a>
              <a href="#" className="social-link">LinkedIn</a>
            </div>
          </Col>
        </Row>
        <hr className="footer-divider" />
        <Row className="text-center">
          <Col>
            <p className="footer-copyright mb-0">&copy; {currentYear} {t("footer_copyright")}</p>
          </Col>
        </Row>
      </Container>
    </motion.footer>
  );
};

export default Footer;
