import React, { useState, useEffect } from "react";
import { Modal, Form, Button, Tabs, Tab, Alert } from "react-bootstrap";
import { useAuth } from "../contexts/AuthContext";
import { authService } from "../services/authService";
import "../styles/AuthModal.css";

const AuthModal = ({ show, handleClose, initialTab = "login" }) => {
  const [activeTab, setActiveTab] = useState(initialTab);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  useEffect(() => {
    if (show) {
      setActiveTab(initialTab);
      setError("");
    }
  }, [show, initialTab]);

  // Login state
  const [loginData, setLoginData] = useState({
    email: "",
    password: "",
  });

  // Sign up state
  const [signupData, setSignupData] = useState({
    fullName: "",
    email: "",
    birthDate: "",
    role: "worker",
    password: "",
    confirmPassword: "",
  });

  const handleLoginChange = (e) => {
    const { name, value } = e.target;
    setLoginData((prev) => ({
      ...prev,
      [name]: value,
    }));
    setError("");
  };

  const handleSignupChange = (e) => {
    const { name, value } = e.target;
    setSignupData((prev) => ({
      ...prev,
      [name]: value,
    }));
    setError("");
  };

  const validateSignupForm = () => {
    if (!signupData.fullName.trim()) {
      setError("Пожалуйста, введите ФИО");
      return false;
    }
    if (!signupData.email.trim()) {
      setError("Пожалуйста, введите почту");
      return false;
    }
    if (!signupData.birthDate) {
      setError("Пожалуйста, выберите дату рождения");
      return false;
    }
    if (signupData.password !== signupData.confirmPassword) {
      setError("Пароли не совпадают");
      return false;
    }
    if (signupData.password.length < 8) {
      setError("Пароль должен быть не менее 8 символов");
      return false;
    }
    return true;
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await authService.login(
        loginData.email,
        loginData.password,
      );

      login(response.user, response.access_token);
      handleClose();

      // Очистка формы
      setLoginData({ email: "", password: "" });
    } catch (err) {
      setError(err.message || "Ошибка входа. Проверьте почту и пароль.");
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e) => {
    e.preventDefault();

    if (!validateSignupForm()) {
      return;
    }

    setError("");
    setLoading(true);

    try {
      const response = await authService.register(signupData);

      login(response.user, response.access_token);
      handleClose();

      // Очистка формы
      setSignupData({
        fullName: "",
        email: "",
        birthDate: "",
        role: "worker",
        password: "",
        confirmPassword: "",
      });
    } catch (err) {
      setError(err.message || "Ошибка регистрации. Попробуйте позже.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      show={show}
      onHide={handleClose}
      centered
      size="lg"
      className="auth-modal"
    >
      <Modal.Header closeButton>
        <Modal.Title className="fw-bold">WellBeing Аутентификация</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {error && <Alert variant="danger">{error}</Alert>}

        <Tabs
          activeKey={activeTab}
          onSelect={(k) => {
            setActiveTab(k);
            setError("");
          }}
          className="mb-3"
        >
          {/* Login Tab */}
          <Tab eventKey="login" title="Вход">
            <Form onSubmit={handleLogin} className="mt-4">
              <Form.Group className="mb-3">
                <Form.Label>Почта</Form.Label>
                <Form.Control
                  type="email"
                  name="email"
                  placeholder="example@email.com"
                  value={loginData.email}
                  onChange={handleLoginChange}
                  required
                  disabled={loading}
                />
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label>Пароль</Form.Label>
                <Form.Control
                  type="password"
                  name="password"
                  placeholder="Введите пароль"
                  value={loginData.password}
                  onChange={handleLoginChange}
                  required
                  disabled={loading}
                />
              </Form.Group>

              <Button
                variant="primary"
                type="submit"
                className="w-100 btn-auth"
                disabled={loading}
              >
                {loading ? "Входим..." : "Войти"}
              </Button>
            </Form>
          </Tab>

          {/* Sign Up Tab */}
          <Tab eventKey="signup" title="Регистрация">
            <Form onSubmit={handleSignup} className="mt-4">
              <Form.Group className="mb-3">
                <Form.Label>ФИО</Form.Label>
                <Form.Control
                  type="text"
                  name="fullName"
                  placeholder="Иван Иванов Иванович"
                  value={signupData.fullName}
                  onChange={handleSignupChange}
                  disabled={loading}
                />
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label>Почта</Form.Label>
                <Form.Control
                  type="email"
                  name="email"
                  placeholder="example@email.com"
                  value={signupData.email}
                  onChange={handleSignupChange}
                  disabled={loading}
                />
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label>Дата рождения</Form.Label>
                <Form.Control
                  type="date"
                  name="birthDate"
                  value={signupData.birthDate}
                  onChange={handleSignupChange}
                  disabled={loading}
                />
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label>Роль</Form.Label>
                <Form.Select
                  name="role"
                  value={signupData.role}
                  onChange={handleSignupChange}
                  disabled={loading}
                >
                  <option value="worker">Рабочий</option>
                  <option value="therapist">Терапевт</option>
                  <option value="admin">Администратор</option>
                </Form.Select>
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label>Пароль</Form.Label>
                <Form.Control
                  type="password"
                  name="password"
                  placeholder="Введите пароль"
                  value={signupData.password}
                  onChange={handleSignupChange}
                  disabled={loading}
                />
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label>Подтверждение пароля</Form.Label>
                <Form.Control
                  type="password"
                  name="confirmPassword"
                  placeholder="Повторите пароль"
                  value={signupData.confirmPassword}
                  onChange={handleSignupChange}
                  disabled={loading}
                />
              </Form.Group>

              <Button
                variant="success"
                type="submit"
                className="w-100 btn-auth"
                disabled={loading}
              >
                {loading ? "Регистрируемся..." : "Создать аккаунт"}
              </Button>
            </Form>
          </Tab>
        </Tabs>
      </Modal.Body>
    </Modal>
  );
};

export default AuthModal;
