import React, { useState } from "react";
import { Navbar, Nav, Button, Container, Dropdown } from "react-bootstrap";
import { useLanguage } from "../contexts/LanguageContext";
import "bootstrap/dist/css/bootstrap.min.css";
import "../styles/App.css";

const NavbarComponent = ({ onLoginClick, onSignUpClick, isLoggedIn, onLogoutClick }) => {
  const [expanded, setExpanded] = useState(false);
  const { t, lang, switchLang } = useLanguage();

  const scrollToSection = (id) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
      setExpanded(false);
    }
  };

  return (
    <Navbar expand="lg" sticky="top" className="navbar-custom shadow-sm">
      <Container>
        <Navbar.Brand href="#" className="fw-bold fs-5 brand-text" onClick={(e) => { e.preventDefault(); window.scrollTo({ top: 0, behavior: "smooth" }); }}>
          WellBeing
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" expanded={expanded.toString()} onClick={() => setExpanded(!expanded)} />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="mx-auto nav-links">
            <Nav.Link onClick={() => scrollToSection("materials")} className="nav-link-item">{t("nav_materials")}</Nav.Link>
            <Nav.Link onClick={() => scrollToSection("test")} className="nav-link-item">{t("nav_test")}</Nav.Link>
            <Nav.Link onClick={() => scrollToSection("ai-assistant")} className="nav-link-item">{t("nav_ai")}</Nav.Link>
            <Nav.Link onClick={() => scrollToSection("mood-journal")} className="nav-link-item">{t("nav_journal")}</Nav.Link>
            <Nav.Link onClick={() => scrollToSection("analytics")} className="nav-link-item">{t("nav_analytics")}</Nav.Link>
          </Nav>
          <div className="d-flex gap-2 justify-content-center justify-content-lg-end flex-wrap align-items-center">
            <Dropdown>
              <Dropdown.Toggle variant="outline-secondary" size="sm">
                {lang === "ru" ? "RU" : "中文"}
              </Dropdown.Toggle>
              <Dropdown.Menu>
                <Dropdown.Item onClick={() => switchLang("ru")}>Русский</Dropdown.Item>
                <Dropdown.Item onClick={() => switchLang("zh")}>中文</Dropdown.Item>
              </Dropdown.Menu>
            </Dropdown>
            {!isLoggedIn ? (
              <>
                <Button variant="outline-primary" className="btn-custom btn-login" onClick={onLoginClick}>{t("nav_login")}</Button>
                <Button variant="primary" className="btn-custom btn-signup" onClick={onSignUpClick}>{t("nav_signup")}</Button>
              </>
            ) : (
              <Button variant="outline-danger" className="btn-custom" onClick={onLogoutClick}>{t("nav_logout")}</Button>
            )}
          </div>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default NavbarComponent;
