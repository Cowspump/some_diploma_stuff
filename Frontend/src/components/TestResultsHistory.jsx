import React, { useState, useEffect } from "react";
import {
  Container,
  Row,
  Col,
  Card,
  Button,
  Badge,
  Modal,
  Alert,
} from "react-bootstrap";
import { getTestResults } from "../services/testService";
import "../styles/TestResultsHistory.css";

const TestResultsHistory = ({ userId }) => {
  const [results, setResults] = useState([]);
  const [selectedResult, setSelectedResult] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    loadResults();
  }, [userId]);

  const loadResults = async () => {
    setLoading(true);
    setError("");
    try {
      const testResults = await getTestResults(userId);
      setResults(
        testResults.sort(
          (a, b) => new Date(b.timestamp) - new Date(a.timestamp),
        ),
      );
    } catch (error) {
      console.error("Error loading results:", error);
      setError("Не удалось загрузить результаты. Попробуйте позже.");
    } finally {
      setLoading(false);
    }
  };

  const getScoreBadge = (score) => {
    if (score >= 80) return <Badge bg="success">Отлично</Badge>;
    if (score >= 60) return <Badge bg="info">Хорошо</Badge>;
    if (score >= 40) return <Badge bg="warning">Средне</Badge>;
    return <Badge bg="danger">Требует внимания</Badge>;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("ru-RU", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const handleViewDetails = (result) => {
    setSelectedResult(result);
    setShowDetailsModal(true);
  };

  const handleRefresh = () => {
    loadResults();
  };

  return (
    <section id="results" className="results-history-section py-5">
      <Container>
        <div className="section-header mb-5">
          <h2 className="section-title">История ваших тестов</h2>
          <p className="section-description">
            Отслеживайте результаты ваших пройденных тестов и смотрите прогресс
          </p>
        </div>

        {error && (
          <Alert variant="danger" className="mb-4">
            {error}
          </Alert>
        )}

        {loading && (
          <Row>
            <Col className="text-center py-5">
              <div className="spinner-border" role="status">
                <span className="visually-hidden">Загрузка...</span>
              </div>
            </Col>
          </Row>
        )}

        {!loading && results.length === 0 && !error ? (
          <Row>
            <Col lg={8} className="mx-auto">
              <Card className="empty-state text-center py-5">
                <Card.Body>
                  <h5 className="mb-3">📊 Нет результатов</h5>
                  <p className="text-muted">
                    Вы еще не прошли ни один тест. Начните тест выше, чтобы
                    увидеть результаты здесь.
                  </p>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        ) : (
          <>
            <Row className="mb-4">
              <Col>
                <div className="d-flex justify-content-between align-items-center">
                  <p className="text-muted mb-0">
                    Всего тестов пройдено: <strong>{results.length}</strong>
                  </p>
                  <Button
                    variant="outline-primary"
                    size="sm"
                    onClick={handleRefresh}
                  >
                    🔄 Обновить
                  </Button>
                </div>
              </Col>
            </Row>

            <Row className="g-4">
              {results.map((result, index) => (
                <Col lg={6} key={result.id}>
                  <Card className="result-card h-100 shadow-sm">
                    <Card.Body>
                      <div className="d-flex justify-content-between align-items-start mb-3">
                        <div>
                          <h5 className="mb-2">
                            Тест #{results.length - index}
                          </h5>
                          <p className="text-muted small mb-0">
                            {formatDate(result.timestamp)}
                          </p>
                        </div>
                        {getScoreBadge(result.score)}
                      </div>

                      <div className="score-display mb-3">
                        <div className="score-circle">
                          <span className="score-value">{result.score}</span>
                          <span className="score-max">/100</span>
                        </div>
                      </div>

                      <div className="progress mb-3">
                        <div
                          className="progress-bar"
                          role="progressbar"
                          style={{ width: `${result.score}%` }}
                          aria-valuenow={result.score}
                          aria-valuemin="0"
                          aria-valuemax="100"
                        ></div>
                      </div>

                      <div className="stats-row mb-3">
                        <span className="stat-item">
                          ✓ Вопросов ответено:{" "}
                          <strong>{Object.keys(result.answers).length}</strong>
                        </span>
                      </div>

                      <Button
                        variant="outline-primary"
                        size="sm"
                        className="w-100"
                        onClick={() => handleViewDetails(result)}
                      >
                        Подробнее →
                      </Button>
                    </Card.Body>
                  </Card>
                </Col>
              ))}
            </Row>
          </>
        )}
      </Container>

      {/* Модальное окно с подробностями */}
      <Modal
        show={showDetailsModal}
        onHide={() => setShowDetailsModal(false)}
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>Результаты теста</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedResult && (
            <div>
              <div className="text-center mb-4">
                <div className="score-circle-large mx-auto mb-3">
                  <span className="score-value-large">
                    {selectedResult.score}
                  </span>
                </div>
                <p className="text-muted">
                  {formatDate(selectedResult.timestamp)}
                </p>
                {getScoreBadge(selectedResult.score)}
              </div>

              <h6 className="mb-3">Ваши ответы:</h6>
              <div className="answers-list">
                {Object.entries(selectedResult.answers).map(
                  ([questionId, answer], index) => (
                    <div
                      key={questionId}
                      className="answer-item p-3 border-bottom"
                    >
                      <p className="mb-2">
                        <strong>Вопрос {index + 1}:</strong>
                      </p>
                      <p className="mb-0 text-primary">✓ {answer}</p>
                    </div>
                  ),
                )}
              </div>
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button
            variant="secondary"
            onClick={() => setShowDetailsModal(false)}
          >
            Закрыть
          </Button>
        </Modal.Footer>
      </Modal>
    </section>
  );
};

export default TestResultsHistory;
