import React, { useState, useEffect } from "react";
import {
  Container,
  Row,
  Col,
  Card,
  Button,
  Nav,
  Navbar,
  Modal,
  Form,
  Alert,
  Table,
  Badge,
} from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { addQuestion, deleteQuestion, fetchTestQuestions } from "../services/testService";
import "../styles/Dashboard.css";

const TherapistDashboard = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [questions, setQuestions] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Форма нового вопроса
  const [newQuestion, setNewQuestion] = useState({
    text: "",
    options: [
      { text: "", points: 0 },
      { text: "", points: 0 },
    ],
  });

  useEffect(() => {
    loadQuestions();
  }, []);

  const loadQuestions = async () => {
    setLoading(true);
    try {
      const data = await fetchTestQuestions();
      setQuestions(data);
    } catch (error) {
      console.error("Error loading questions:", error);
      setError("Не удалось загрузить вопросы");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    onLogout();
    navigate("/");
  };

  const handleAddOption = () => {
    setNewQuestion({
      ...newQuestion,
      options: [...newQuestion.options, { text: "", points: 0 }],
    });
  };

  const handleRemoveOption = (index) => {
    const updatedOptions = newQuestion.options.filter((_, i) => i !== index);
    setNewQuestion({ ...newQuestion, options: updatedOptions });
  };

  const handleOptionChange = (index, field, value) => {
    const updatedOptions = [...newQuestion.options];
    updatedOptions[index][field] = field === "points" ? parseInt(value) || 0 : value;
    setNewQuestion({ ...newQuestion, options: updatedOptions });
  };

  const handleSubmitQuestion = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!newQuestion.text.trim()) {
      setError("Введите текст вопроса");
      return;
    }

    if (newQuestion.options.length < 2) {
      setError("Добавьте минимум 2 варианта ответа");
      return;
    }

    for (const option of newQuestion.options) {
      if (!option.text.trim()) {
        setError("Заполните все варианты ответов");
        return;
      }
    }

    setLoading(true);
    try {
      await addQuestion(newQuestion);
      setSuccess("Вопрос успешно добавлен!");
      setShowAddModal(false);
      setNewQuestion({
        text: "",
        options: [
          { text: "", points: 0 },
          { text: "", points: 0 },
        ],
      });
      await loadQuestions();
    } catch (error) {
      console.error("Error adding question:", error);
      setError(error.message || "Не удалось добавить вопрос");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteQuestion = async (questionId) => {
    if (!window.confirm("Вы уверены, что хотите удалить этот вопрос?")) {
      return;
    }

    setLoading(true);
    try {
      await deleteQuestion(questionId);
      setSuccess("Вопрос успешно удален!");
      await loadQuestions();
    } catch (error) {
      console.error("Error deleting question:", error);
      setError(error.message || "Не удалось удалить вопрос");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <Navbar className="navbar-custom shadow-sm" sticky="top">
        <Container>
          <Navbar.Brand className="fw-bold fs-5">
            ✨ WellBeing - Панель терапевта
          </Navbar.Brand>
          <Nav className="ms-auto">
            <div className="user-info">
              <span className="me-3">
                Добро пожаловать, {user?.fullName || user?.email}!
              </span>
              <Button variant="outline-danger" size="sm" onClick={handleLogout}>
                Выход
              </Button>
            </div>
          </Nav>
        </Container>
      </Navbar>

      <Container className="mt-5">
        {error && <Alert variant="danger" dismissible onClose={() => setError("")}>{error}</Alert>}
        {success && <Alert variant="success" dismissible onClose={() => setSuccess("")}>{success}</Alert>}

        <Row className="mb-4">
          <Col>
            <div className="d-flex justify-content-between align-items-center">
              <h2>Управление вопросами тестов</h2>
              <Button variant="primary" onClick={() => setShowAddModal(true)}>
                + Добавить вопрос
              </Button>
            </div>
          </Col>
        </Row>

        {loading && questions.length === 0 ? (
          <div className="text-center py-5">
            <div className="spinner-border" role="status">
              <span className="visually-hidden">Загрузка...</span>
            </div>
          </div>
        ) : (
          <Row>
            <Col>
              <Card>
                <Card.Body>
                  {questions.length === 0 ? (
                    <div className="text-center py-5 text-muted">
                      <p>Нет вопросов. Добавьте первый вопрос!</p>
                    </div>
                  ) : (
                    <Table responsive hover>
                      <thead>
                        <tr>
                          <th>#</th>
                          <th>Вопрос</th>
                          <th>Варианты ответов</th>
                          <th>Действия</th>
                        </tr>
                      </thead>
                      <tbody>
                        {questions.map((question, index) => (
                          <tr key={question.id}>
                            <td>{index + 1}</td>
                            <td>{question.text}</td>
                            <td>
                              <ul className="mb-0 ps-3">
                                {question.options.map((option, optIndex) => (
                                  <li key={optIndex}>
                                    {option.text} <Badge bg="secondary">({option.points} баллов)</Badge>
                                  </li>
                                ))}
                              </ul>
                            </td>
                            <td>
                              <Button
                                variant="outline-danger"
                                size="sm"
                                onClick={() => handleDeleteQuestion(question.id)}
                                disabled={loading}
                              >
                                Удалить
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  )}
                </Card.Body>
              </Card>
            </Col>
          </Row>
        )}
      </Container>

      {/* Модальное окно добавления вопроса */}
      <Modal show={showAddModal} onHide={() => setShowAddModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Добавить новый вопрос</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form onSubmit={handleSubmitQuestion}>
            <Form.Group className="mb-3">
              <Form.Label>Текст вопроса</Form.Label>
              <Form.Control
                type="text"
                placeholder="Введите вопрос"
                value={newQuestion.text}
                onChange={(e) => setNewQuestion({ ...newQuestion, text: e.target.value })}
                disabled={loading}
              />
            </Form.Group>

            <Form.Label>Варианты ответов</Form.Label>
            {newQuestion.options.map((option, index) => (
              <Row key={index} className="mb-3">
                <Col md={8}>
                  <Form.Control
                    type="text"
                    placeholder="Текст ответа"
                    value={option.text}
                    onChange={(e) => handleOptionChange(index, "text", e.target.value)}
                    disabled={loading}
                  />
                </Col>
                <Col md={3}>
                  <Form.Control
                    type="number"
                    placeholder="Баллы"
                    value={option.points}
                    onChange={(e) => handleOptionChange(index, "points", e.target.value)}
                    disabled={loading}
                  />
                </Col>
                <Col md={1}>
                  {newQuestion.options.length > 2 && (
                    <Button
                      variant="outline-danger"
                      size="sm"
                      onClick={() => handleRemoveOption(index)}
                      disabled={loading}
                    >
                      ✕
                    </Button>
                  )}
                </Col>
              </Row>
            ))}

            <Button
              variant="outline-secondary"
              size="sm"
              onClick={handleAddOption}
              className="mb-3"
              disabled={loading}
            >
              + Добавить вариант
            </Button>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowAddModal(false)} disabled={loading}>
            Отмена
          </Button>
          <Button variant="primary" onClick={handleSubmitQuestion} disabled={loading}>
            {loading ? "Сохранение..." : "Сохранить"}
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default TherapistDashboard;
