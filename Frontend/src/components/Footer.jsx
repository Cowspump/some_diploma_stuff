import React from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import '../styles/App.css';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="footer-section py-5 mt-5">
      <Container>
        <Row className="g-4 mb-5">
          <Col md={6} lg={3}>
            <h6 className="footer-title mb-3">About</h6>
            <ul className="footer-links">
              <li><a href="#" className="footer-link">About Us</a></li>
              <li><a href="#" className="footer-link">Our Mission</a></li>
              <li><a href="#" className="footer-link">Research</a></li>
            </ul>
          </Col>

          <Col md={6} lg={3}>
            <h6 className="footer-title mb-3">Resources</h6>
            <ul className="footer-links">
              <li><a href="#" className="footer-link">Blog</a></li>
              <li><a href="#" className="footer-link">Guides</a></li>
              <li><a href="#" className="footer-link">FAQ</a></li>
            </ul>
          </Col>

          <Col md={6} lg={3}>
            <h6 className="footer-title mb-3">Legal</h6>
            <ul className="footer-links">
              <li><a href="#" className="footer-link">Privacy Policy</a></li>
              <li><a href="#" className="footer-link">Terms of Service</a></li>
              <li><a href="#" className="footer-link">Contact</a></li>
            </ul>
          </Col>

          <Col md={6} lg={3}>
            <h6 className="footer-title mb-3">Follow Us</h6>
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
            <p className="footer-copyright mb-0">
              © {currentYear} WellBeing. All rights reserved.
            </p>
          </Col>
        </Row>
      </Container>
    </footer>
  );
};

export default Footer;