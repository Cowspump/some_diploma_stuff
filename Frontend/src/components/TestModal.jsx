import React, { useState, useEffect } from "react";
import {
  Modal, Button, Form, ProgressBar, Alert, Spinner, Card, Row, Col, Badge, Accordion,
} from "react-bootstrap";
import { fetchTestQuestions, saveTestResult, getTests, explainQuestion } from "../services/testService";
import { useLanguage } from "../contexts/LanguageContext";
import "../styles/TestModal.css";

const TestModal = ({ show, onHide, userId }) => {
  const { t } = useLanguage();
  const [tests, setTests] = useState([]);
  const [selectedTest, setSelectedTest] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [submitted, setSubmitted] = useState(false);
  const [score, setScore] = useState(0);
  const [error, setError] = useState("");
  // AI analysis after test
  const [explanations, setExplanations] = useState({});
  const [explainLoadingId, setExplainLoadingId] = useState(null);
  const [allExplainLoading, setAllExplainLoading] = useState(false);

  useEffect(() => {
    if (show) {
      loadTests();
      setSelectedTest(null);
      setQuestions([]);
      setCurrentQuestion(0);
      setAnswers({});
      setSubmitted(false);
      setScore(0);
      setExplanations({});
    }
  }, [show]);

  const loadTests = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getTests();
      setTests(data);
    } catch (err) {
      setError(t("test_load_error"));
    } finally {
      setLoading(false);
    }
  };

  const handleSelectTest = async (test) => {
    setSelectedTest(test);
    setLoading(true);
    setError("");
    try {
      const data = await fetchTestQuestions(test.id);
      if (data.length === 0) {
        setError(t("test_no_questions"));
        setQuestions([]);
      } else {
        setQuestions(data);
        setCurrentQuestion(0);
        setAnswers({});
      }
    } catch (err) {
      setError(t("test_questions_error"));
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setSelectedTest(null);
    setQuestions([]);
    setCurrentQuestion(0);
    setAnswers({});
    setError("");
    setExplanations({});
  };

  const handleAnswerChange = (optionIndex) => {
    setAnswers({ ...answers, [questions[currentQuestion].id]: optionIndex });
  };

  const handleNext = () => {
    if (currentQuestion < questions.length - 1) setCurrentQuestion(currentQuestion + 1);
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) setCurrentQuestion(currentQuestion - 1);
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const response = await saveTestResult(answers, selectedTest?.id);
      setScore(response.total_score || 0);
      setSubmitted(true);
    } catch (err) {
      setError(t("test_save_error"));
    } finally {
      setLoading(false);
    }
  };

  // AI analysis for a single question (after test)
  const handleExplainOne = async (questionId) => {
    setExplainLoadingId(questionId);
    try {
      const res = await explainQuestion(questionId);
      setExplanations((prev) => ({ ...prev, [questionId]: res.explanation }));
    } catch (err) {
      setExplanations((prev) => ({ ...prev, [questionId]: "Ошибка при запросе объяснения." }));
    } finally {
      setExplainLoadingId(null);
    }
  };

  // AI analysis for ALL questions at once
  const handleExplainAll = async () => {
    setAllExplainLoading(true);
    for (const q of questions) {
      if (!explanations[q.id]) {
        try {
          const res = await explainQuestion(q.id);
          setExplanations((prev) => ({ ...prev, [q.id]: res.explanation }));
        } catch {
          setExplanations((prev) => ({ ...prev, [q.id]: "Ошибка" }));
        }
      }
    }
    setAllExplainLoading(false);
  };

  const handleClose = () => {
    onHide();
    setSubmitted(false);
    setSelectedTest(null);
    setExplanations({});
  };

  if (loading) {
    return (
      <Modal show={show} onHide={onHide} centered>
        <Modal.Body className="text-center py-5"><Spinner animation="border" /></Modal.Body>
      </Modal>
    );
  }

  return (
    <Modal show={show} onHide={handleClose} centered size="lg">
      <Modal.Header closeButton>
        <Modal.Title>
          {submitted ? t("test_result") : selectedTest ? selectedTest.title : t("test_select")}
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {error && <Alert variant="danger" className="mb-3">{error}</Alert>}

        {/* Test selection */}
        {!selectedTest && !submitted && (
          <Row className="g-3">
            {tests.length === 0 ? (
              <Col><p className="text-muted text-center">{t("test_no_tests")}</p></Col>
            ) : tests.map((test) => (
              <Col md={6} key={test.id}>
                <Card className="h-100 shadow-sm" style={{ cursor: "pointer" }} onClick={() => handleSelectTest(test)}>
                  <Card.Body>
                    <Card.Title>{test.title}</Card.Title>
                    {test.description && <Card.Text className="text-muted small">{test.description}</Card.Text>}
                    <Badge bg="secondary">{test.question_count} {t("test_questions_count")}</Badge>
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>
        )}

        {/* Taking the test */}
        {selectedTest && !submitted && questions.length > 0 && (
          <>
            <ProgressBar now={((currentQuestion + 1) / questions.length) * 100} label={`${currentQuestion + 1}/${questions.length}`} className="mb-4" />
            <h5 className="mb-3">{questions[currentQuestion].text}</h5>
            <Form>
              {questions[currentQuestion].options.map((option, idx) => (
                <Form.Check key={idx} type="radio" name="answer" label={option.text} value={idx}
                  onChange={() => handleAnswerChange(idx)}
                  checked={answers[questions[currentQuestion].id] === idx}
                  className="mb-2" />
              ))}
            </Form>
          </>
        )}

        {/* Results + AI analysis */}
        {submitted && (
          <div>
            <div className="text-center py-3">
              <h4 className="mb-3">{t("test_completed")}</h4>
              <p className="mb-2">{t("test_your_score")} <strong>{score} {t("test_points")}</strong></p>
              <p className="text-muted">{t("test_saved")}</p>
            </div>

            <hr />

            <div className="d-flex justify-content-between align-items-center mb-3">
              <h5 className="mb-0">{t("test_ai_analysis")}</h5>
              <Button variant="outline-info" size="sm" onClick={handleExplainAll} disabled={allExplainLoading}>
                {allExplainLoading ? <><Spinner animation="border" size="sm" className="me-1" /> {t("test_analyzing")}</> : t("test_get_analysis")}
              </Button>
            </div>

            <Accordion>
              {questions.map((q, idx) => (
                <Accordion.Item eventKey={String(q.id)} key={q.id}>
                  <Accordion.Header>
                    <span className="me-2"><Badge bg="secondary">{idx + 1}</Badge></span>
                    {q.text}
                    {answers[q.id] !== undefined && (
                      <Badge bg="primary" className="ms-2">
                        {q.options[answers[q.id]]?.text}
                      </Badge>
                    )}
                  </Accordion.Header>
                  <Accordion.Body>
                    <p className="mb-2"><strong>{t("therapist_q_options")}:</strong></p>
                    <ul>
                      {q.options.map((opt, oi) => (
                        <li key={oi} className={answers[q.id] === oi ? "fw-bold" : ""}>
                          {opt.text} ({opt.points} {t("test_points")})
                          {answers[q.id] === oi && " ← "}
                        </li>
                      ))}
                    </ul>
                    {explanations[q.id] ? (
                      <Alert variant="info" className="mt-2 mb-0">{explanations[q.id]}</Alert>
                    ) : (
                      <Button variant="outline-info" size="sm" onClick={() => handleExplainOne(q.id)} disabled={explainLoadingId === q.id}>
                        {explainLoadingId === q.id ? <Spinner animation="border" size="sm" /> : "AI"}
                      </Button>
                    )}
                  </Accordion.Body>
                </Accordion.Item>
              ))}
            </Accordion>
          </div>
        )}
      </Modal.Body>
      <Modal.Footer>
        {!submitted && selectedTest && questions.length > 0 ? (
          <>
            <Button variant="outline-secondary" size="sm" onClick={handleBack}>{t("test_back_to_list")}</Button>
            <Button variant="secondary" onClick={handlePrevious} disabled={currentQuestion === 0}>{t("test_prev")}</Button>
            {currentQuestion === questions.length - 1 ? (
              <Button variant="primary" onClick={handleSubmit} disabled={answers[questions[currentQuestion]?.id] === undefined}>{t("test_finish")}</Button>
            ) : (
              <Button variant="primary" onClick={handleNext} disabled={answers[questions[currentQuestion]?.id] === undefined}>{t("test_next")}</Button>
            )}
          </>
        ) : (
          <Button variant="primary" onClick={handleClose}>{t("test_close")}</Button>
        )}
      </Modal.Footer>
    </Modal>
  );
};

export default TestModal;
