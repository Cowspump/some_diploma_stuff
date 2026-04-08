import React, { useState, useEffect } from "react";
import { Modal, Form, Button, Tabs, Tab, Alert } from "react-bootstrap";
import { useAuth } from "../contexts/AuthContext";
import { useLanguage } from "../contexts/LanguageContext";
import { authService } from "../services/authService";
import "../styles/AuthModal.css";

const AuthModal = ({ show, handleClose, initialTab = "login", onLoginSuccess }) => {
  const [activeTab, setActiveTab] = useState(initialTab);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [showResetForm, setShowResetForm] = useState(false);
  const { login } = useAuth();
  const { t } = useLanguage();

  const [resetData, setResetData] = useState({ email: "", newPassword: "", confirmPassword: "" });

  useEffect(() => {
    if (show) {
      setActiveTab(initialTab);
      setError("");
      setSuccess("");
      setShowResetForm(false);
    }
  }, [show, initialTab]);

  const [loginData, setLoginData] = useState({ email: "", password: "" });
  const [signupData, setSignupData] = useState({
    fullName: "",
    email: "",
    role: "worker",
    password: "",
    confirmPassword: "",
  });

  const handleLoginChange = (e) => {
    setLoginData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError("");
  };

  const handleSignupChange = (e) => {
    setSignupData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError("");
  };

  const handleResetChange = (e) => {
    setResetData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError("");
  };

  const validateSignupForm = () => {
    if (!signupData.fullName.trim()) { setError(t("auth_err_fullname")); return false; }
    if (!signupData.email.trim()) { setError(t("auth_err_email")); return false; }
    if (signupData.password !== signupData.confirmPassword) { setError(t("auth_err_password_match")); return false; }
    if (signupData.password.length < 8) { setError(t("auth_err_password_length")); return false; }
    return true;
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const response = await authService.login(loginData.email, loginData.password);
      login(response.user, response.access_token);
      setLoginData({ email: "", password: "" });
      if (onLoginSuccess) onLoginSuccess();
      else handleClose();
    } catch (err) {
      setError(err.message || t("auth_err_login"));
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    if (!validateSignupForm()) return;
    setError("");
    setLoading(true);
    try {
      await authService.register(signupData);
      const loginResponse = await authService.login(signupData.email, signupData.password);
      login(loginResponse.user, loginResponse.access_token);
      setSignupData({ fullName: "", email: "", role: "worker", password: "", confirmPassword: "" });
      if (onLoginSuccess) onLoginSuccess();
      else handleClose();
    } catch (err) {
      setError(err.message || t("auth_err_signup"));
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (!resetData.email.trim()) { setError(t("auth_err_email")); return; }
    if (resetData.newPassword.length < 8) { setError(t("auth_err_password_length")); return; }
    if (resetData.newPassword !== resetData.confirmPassword) { setError(t("auth_err_password_match")); return; }
    setLoading(true);
    try {
      await authService.resetPassword(resetData.email, resetData.newPassword);
      setSuccess(t("auth_reset_success"));
      setResetData({ email: "", newPassword: "", confirmPassword: "" });
      setTimeout(() => {
        setShowResetForm(false);
        setSuccess("");
      }, 2000);
    } catch (err) {
      setError(err.message || t("auth_reset_error"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal show={show} onHide={handleClose} centered size="lg" className="auth-modal">
      <Modal.Header closeButton>
        <Modal.Title className="fw-bold">
          {showResetForm ? t("auth_reset_title") : t("auth_title")}
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {error && <Alert variant="danger">{error}</Alert>}
        {success && <Alert variant="success">{success}</Alert>}

        {showResetForm ? (
          <div className="reset-form-wrapper">
            <p style={{ color: "#a1a1b5", marginBottom: "1.5rem", fontSize: "0.95rem" }}>
              {t("auth_reset_desc")}
            </p>
            <Form onSubmit={handleResetPassword}>
              <Form.Group className="mb-3">
                <Form.Label>{t("auth_email")}</Form.Label>
                <Form.Control type="email" name="email" placeholder={t("auth_email_placeholder")} value={resetData.email} onChange={handleResetChange} required disabled={loading} />
              </Form.Group>
              <Form.Group className="mb-3">
                <Form.Label>{t("auth_new_password")}</Form.Label>
                <Form.Control type="password" name="newPassword" placeholder={t("auth_new_password_placeholder")} value={resetData.newPassword} onChange={handleResetChange} required disabled={loading} />
              </Form.Group>
              <Form.Group className="mb-3">
                <Form.Label>{t("auth_confirm_password")}</Form.Label>
                <Form.Control type="password" name="confirmPassword" placeholder={t("auth_confirm_placeholder")} value={resetData.confirmPassword} onChange={handleResetChange} required disabled={loading} />
              </Form.Group>
              <Button variant="primary" type="submit" className="w-100 btn-auth" disabled={loading}>
                {loading ? t("auth_resetting") : t("auth_reset_btn")}
              </Button>
            </Form>
            <div className="text-center mt-3">
              <button className="back-to-login" onClick={() => { setShowResetForm(false); setError(""); setSuccess(""); }}>
                {t("auth_back_to_login")}
              </button>
            </div>
          </div>
        ) : (
          <Tabs activeKey={activeTab} onSelect={(k) => { setActiveTab(k); setError(""); }} className="mb-3">
            <Tab eventKey="login" title={t("auth_login_tab")}>
              <Form onSubmit={handleLogin} className="mt-4">
                <Form.Group className="mb-3">
                  <Form.Label>{t("auth_email")}</Form.Label>
                  <Form.Control type="email" name="email" placeholder={t("auth_email_placeholder")} value={loginData.email} onChange={handleLoginChange} required disabled={loading} />
                </Form.Group>
                <Form.Group className="mb-3">
                  <Form.Label>{t("auth_password")}</Form.Label>
                  <Form.Control type="password" name="password" placeholder={t("auth_password_placeholder")} value={loginData.password} onChange={handleLoginChange} required disabled={loading} />
                </Form.Group>
                <div className="text-end mb-2">
                  <span className="forgot-password-link" onClick={() => { setShowResetForm(true); setError(""); }}>
                    {t("auth_forgot_password")}
                  </span>
                </div>
                <Button variant="primary" type="submit" className="w-100 btn-auth" disabled={loading}>
                  {loading ? t("auth_logging_in") : t("auth_login_btn")}
                </Button>
              </Form>
            </Tab>
            <Tab eventKey="signup" title={t("auth_signup_tab")}>
              <Form onSubmit={handleSignup} className="mt-4">
                <Form.Group className="mb-3">
                  <Form.Label>{t("auth_fullname")}</Form.Label>
                  <Form.Control type="text" name="fullName" placeholder={t("auth_fullname_placeholder")} value={signupData.fullName} onChange={handleSignupChange} disabled={loading} />
                </Form.Group>
                <Form.Group className="mb-3">
                  <Form.Label>{t("auth_email")}</Form.Label>
                  <Form.Control type="email" name="email" placeholder={t("auth_email_placeholder")} value={signupData.email} onChange={handleSignupChange} disabled={loading} />
                </Form.Group>
                <Form.Group className="mb-3">
                  <Form.Label>{t("auth_role")}</Form.Label>
                  <Form.Select name="role" value={signupData.role} onChange={handleSignupChange} disabled={loading}>
                    <option value="worker">{t("auth_role_worker")}</option>
                    <option value="therapist">{t("auth_role_therapist")}</option>
                  </Form.Select>
                </Form.Group>
                <Form.Group className="mb-3">
                  <Form.Label>{t("auth_password")}</Form.Label>
                  <Form.Control type="password" name="password" placeholder={t("auth_password_placeholder")} value={signupData.password} onChange={handleSignupChange} disabled={loading} />
                </Form.Group>
                <Form.Group className="mb-3">
                  <Form.Label>{t("auth_confirm_password")}</Form.Label>
                  <Form.Control type="password" name="confirmPassword" placeholder={t("auth_confirm_placeholder")} value={signupData.confirmPassword} onChange={handleSignupChange} disabled={loading} />
                </Form.Group>
                <Button variant="success" type="submit" className="w-100 btn-auth" disabled={loading}>
                  {loading ? t("auth_signing_up") : t("auth_signup_btn")}
                </Button>
              </Form>
            </Tab>
          </Tabs>
        )}
      </Modal.Body>
    </Modal>
  );
};

export default AuthModal;
