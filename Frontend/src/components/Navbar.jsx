import React, { useState } from 'react';
import { Navbar, Nav, Button, Container } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import '../styles/App.css';

const NavbarComponent = ({ onLoginClick, onSignUpClick, isLoggedIn, onLogoutClick }) => {
  const [expanded, setExpanded] = useState(false);

  const scrollToSection = (id) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      setExpanded(false);
    }
  };

  return (
    <Navbar
      expand="lg"
      sticky="top"
      className="navbar-custom shadow-sm"
    >
      <Container>
        <Navbar.Brand
          href="#"
          className="fw-bold fs-5 brand-text"
          onClick={(e) => {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }}
        >
          ✨ WellBeing
        </Navbar.Brand>

        <Navbar.Toggle
          aria-controls="basic-navbar-nav"
          expanded={expanded}
          onClick={() => setExpanded(expanded ? false : true)}
        />

        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="mx-auto nav-links">
            <Nav.Link
              onClick={() => scrollToSection('materials')}
              className="nav-link-item"
            >
              Materials
            </Nav.Link>
            <Nav.Link
              onClick={() => scrollToSection('test')}
              className="nav-link-item"
            >
              Test
            </Nav.Link>
            <Nav.Link
              onClick={() => scrollToSection('ai-assistant')}
              className="nav-link-item"
            >
              AI Assistant
            </Nav.Link>
            <Nav.Link
              onClick={() => scrollToSection('mood-journal')}
              className="nav-link-item"
            >
              Journal
            </Nav.Link>
            <Nav.Link
              onClick={() => scrollToSection('analytics')}
              className="nav-link-item"
            >
              Analytics
            </Nav.Link>
          </Nav>

          <div className="d-flex gap-2 justify-content-center justify-content-lg-end flex-wrap">
            {!isLoggedIn ? (
              <>
                <Button
                  variant="outline-primary"
                  className="btn-custom btn-login"
                  onClick={onLoginClick}
                >
                  Login
                </Button>
                <Button
                  variant="primary"
                  className="btn-custom btn-signup"
                  onClick={onSignUpClick}
                >
                  Sign Up
                </Button>
              </>
            ) : (
              <Button
                variant="outline-danger"
                className="btn-custom"
                onClick={onLogoutClick}
              >
                Logout
              </Button>
            )}
          </div>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default NavbarComponent;