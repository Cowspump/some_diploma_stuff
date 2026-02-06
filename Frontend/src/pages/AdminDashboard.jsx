import React from 'react';
import { Container, Row, Col, Card, Button, Nav, Navbar } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import '../styles/Dashboard.css';

const AdminDashboard = ({ user, onLogout }) => {
  const navigate = useNavigate();

  const handleLogout = () => {
    onLogout();
    navigate('/');
  };

  return (
    <div className="dashboard">
      <Navbar className="navbar-custom shadow-sm" sticky="top">
        <Container>
          <Navbar.Brand className="fw-bold fs-5">
            ✨ WellBeing - Админ панель
          </Navbar.Brand>
          <Nav className="ms-auto">
            <div className="user-info">
              <span className="me-3">Добро пожаловать, {user?.fullName || user?.email}!</span>
              <Button variant="outline-danger" size="sm" onClick={handleLogout}>
                Выход
              </Button>
            </div>
          </Nav>
        </Container>
      </Navbar>

      <Container className="mt-5">
        <Row>
          <Col md={3} className="mb-4">
            <Card className="dashboard-card">
              <Card.Body>
                <Card.Title>Пользователи</Card.Title>
                <Card.Text>Управление профилями пользователей</Card.Text>
                <Button variant="primary">Перейти</Button>
              </Card.Body>
            </Card>
          </Col>

          <Col md={3} className="mb-4">
            <Card className="dashboard-card">
              <Card.Body>
                <Card.Title>Тесты</Card.Title>
                <Card.Text>Управление тестами и вопросами</Card.Text>
                <Button variant="primary">Перейти</Button>
              </Card.Body>
            </Card>
          </Col>

          <Col md={3} className="mb-4">
            <Card className="dashboard-card">
              <Card.Body>
                <Card.Title>Отчёты</Card.Title>
                <Card.Text>Просмотр статистики и аналитики</Card.Text>
                <Button variant="primary">Перейти</Button>
              </Card.Body>
            </Card>
          </Col>

          <Col md={3} className="mb-4">
            <Card className="dashboard-card">
              <Card.Body>
                <Card.Title>Настройки</Card.Title>
                <Card.Text>Настройки системы</Card.Text>
                <Button variant="primary">Перейти</Button>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
};

export default AdminDashboard;