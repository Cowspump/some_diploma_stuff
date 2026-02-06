import React, { useState, useEffect } from "react";
import { Modal, Button, Form, ProgressBar, Alert } from "react-bootstrap";
import { fetchTestQuestions, saveTestResult } from "../services/testService";
import "../styles/TestModal.css";

const TestModal = ({ show, onHide, userId }) => {
  const [questions, setQuestions] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [submitted, setSubmitted] = useState(false);
  const [score, setScore] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    if (show) {
      loadQuestions();
    }
  }, [show]);

  const loadQuestions = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchTestQuestions();
      setQuestions(data);
      setCurrentQuestion(0);
      setAnswers({});
      setSubmitted(false);
      setScore(0);
    } catch (error) {
      console.error("Ошибка загрузки вопросов:", error);
      setError("Не удалось загрузить вопросы. Попробуйте позже.");
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (e) => {
    setAnswers({
      ...answers,
      [questions[currentQuestion].id]: e.target.value,
    });
  };

  const handleNext = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const handleSubmit = async () => {
    const calculatedScore =
      Object.keys(answers).length === questions.length ? 75 : 50;
    setScore(calculatedScore);
    setLoading(true);

    try {
      await saveTestResult(userId || "guest", answers, calculatedScore);
      setSubmitted(true);
    } catch (error) {
      console.error("Ошибка сохранения результата:", error);
      setError("Не удалось сохранить результат. Попробуйте позже.");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    onHide();
    setSubmitted(false);
  };

  if (loading) {
    return (
      <Modal show={show} onHide={onHide} centered>
        <Modal.Body className="text-center py-5">
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Загрузка...</span>
          </div>
        </Modal.Body>
      </Modal>
    );
  }

  return (
    <Modal show={show} onHide={handleClose} centered size="lg">
      <Modal.Header closeButton>
        <Modal.Title>Тест благополучия</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {error && (
          <Alert variant="danger" className="mb-3">
            {error}
          </Alert>
        )}
        {!submitted ? (
          <>
            <ProgressBar
              now={((currentQuestion + 1) / questions.length) * 100}
              label={`${currentQuestion + 1}/${questions.length}`}
              className="mb-4"
            />

            {questions.length > 0 && (
              <div>
                <h5 className="mb-3">{questions[currentQuestion].question}</h5>
                <Form>
                  {questions[currentQuestion].options.map((option, idx) => (
                    <Form.Check
                      key={idx}
                      type="radio"
                      name="answer"
                      label={option}
                      value={option}
                      onChange={handleAnswerChange}
                      checked={
                        answers[questions[currentQuestion].id] === option
                      }
                      className="mb-2"
                    />
                  ))}
                </Form>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-4">
            <h4 className="mb-3">Тест завершен! 🎉</h4>
            <p className="mb-4">
              Ваш результат: <strong>{score} баллов</strong>
            </p>
            <p className="text-muted">Результат сохранен в вашем профиле</p>
          </div>
        )}
      </Modal.Body>
      <Modal.Footer>
        {!submitted ? (
          <>
            <Button
              variant="secondary"
              onClick={handlePrevious}
              disabled={currentQuestion === 0}
            >
              ← Назад
            </Button>
            {currentQuestion === questions.length - 1 ? (
              <Button
                variant="primary"
                onClick={handleSubmit}
                disabled={!answers[questions[currentQuestion].id]}
              >
                Завершить →
              </Button>
            ) : (
              <Button
                variant="primary"
                onClick={handleNext}
                disabled={!answers[questions[currentQuestion].id]}
              >
                Далее →
              </Button>
            )}
          </>
        ) : (
          <Button variant="primary" onClick={handleClose}>
            Закрыть
          </Button>
        )}
      </Modal.Footer>
    </Modal>
  );
};

export default TestModal;
