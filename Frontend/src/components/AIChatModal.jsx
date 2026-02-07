// src/components/AIChatModal.jsx
import React, { useState, useRef, useEffect } from "react";
import { Modal, Form, Button, Spinner, Alert } from "react-bootstrap";
import { apiService } from "../services/api";
import "../styles/AIChatModal.css";

const AIChatModal = ({
  show,
  onHide,
  journalHistory: initialJournalHistory,
  testResults: initialTestResults,
}) => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Привет! Я ваш ИИ-помощник. Я проанализировал вашу историю и готов помочь вам. Какие у вас есть вопросы?",
      sender: "ai",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [journalHistory, setJournalHistory] = useState(
    initialJournalHistory || [],
  );
  const [testResults, setTestResults] = useState(initialTestResults || []);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (
      show &&
      (!initialJournalHistory || initialJournalHistory.length === 0)
    ) {
      loadData();
    } else {
      setJournalHistory(initialJournalHistory || []);
      setTestResults(initialTestResults || []);
    }
  }, [show, initialJournalHistory, initialTestResults]);

  const loadData = async () => {
    try {
      const journalRes = await apiService.get("/journal");
      setJournalHistory(journalRes.journals || []);

      const testsRes = await apiService.get("/test-results");
      setTestResults(testsRes.results || []);
    } catch (err) {
      console.error("Error loading data for AI Assistant:", err);
    }
  };

  // Генерируем рекомендации на основе истории
  const generateRecommendations = () => {
    const recommendations = [];

    // Анализ результатов тестов
    if (testResults && testResults.length > 0) {
      const avgScore =
        testResults.reduce((sum, test) => sum + (test.total_score || 0), 0) /
        testResults.length;

      if (avgScore < 50) {
        recommendations.push({
          id: 1,
          title: "⚠️ Повышенный стресс",
          description:
            "Ваши результаты показывают высокий уровень стресса. Рекомендуем регулярные паузы и медитацию.",
          category: "urgency",
        });
      }

      recommendations.push({
        id: 2,
        title: "📊 Анализ тренда",
        description: `Ваш средний результат: ${avgScore.toFixed(1)}. Тренд: ${testResults.length > 1 ? "улучшается ✅" : "начальные данные"}`,
        category: "analytics",
      });
    }

    // Анализ настроений из журнала
    if (journalHistory && journalHistory.length > 0) {
      const moods = journalHistory.map((entry) => entry.wellbeing_score || 0);
      const hasNegativeMoods = moods.some((mood) => mood <= 2);

      if (hasNegativeMoods) {
        recommendations.push({
          id: 3,
          title: "💭 Здоровье психики",
          description:
            "Заметили периоды с негативными эмоциями. Попробуйте техники осознанности.",
          category: "wellness",
        });
      }

      recommendations.push({
        id: 4,
        title: "📝 Последняя запись",
        description: `"${journalHistory[0]?.note_text?.substring(0, 50) || "Нет текста"}..."`,
        category: "journal",
      });
    }

    // Стандартные рекомендации
    if (recommendations.length === 0) {
      recommendations.push({
        id: 5,
        title: "🎯 Начните с основ",
        description:
          "Заполните журнал настроений и пройдите тесты для получения персональных рекомендаций.",
        category: "general",
      });
    }

    return recommendations;
  };

  const handleSendMessage = async () => {
    if (inputValue.trim() === "") return;

    const userMessageText = inputValue;

    // Добавляем сообщение пользователя
    const userMessage = {
      id: messages.length + 1,
      text: userMessageText,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages([...messages, userMessage]);
    setInputValue("");
    setIsLoading(true);
    setError("");

    try {
      // Backend ожидает JSON body с полем prompt
      const response = await apiService.post("/ai/ask", {
        prompt: userMessageText,
      });

      const aiMessage = {
        id: messages.length + 2,
        text: response.response || "Не удалось получить ответ",
        sender: "ai",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("Error sending message to AI:", error);
      setError("Не удалось получить ответ от ИИ-ассистента");

      const errorMessage = {
        id: messages.length + 2,
        text: "Извините, произошла ошибка при обработке вашего запроса. Попробуйте еще раз.",
        sender: "ai",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const recommendations = generateRecommendations();

  return (
    <Modal show={show} onHide={onHide} size="xl" className="ai-chat-modal">
      <Modal.Header closeButton>
        <Modal.Title>AI Ассистент</Modal.Title>
      </Modal.Header>
      <Modal.Body className="ai-chat-body p-0">
        <div className="chat-container">
          {/* Левая часть - Рекомендации */}
          <div className="recommendations-panel">
            <div className="recommendations-header">
              <h5>📋 Рекомендации</h5>
              <small className="text-muted">На основе вашей истории</small>
            </div>
            <div className="recommendations-list">
              {recommendations.map((rec) => (
                <div
                  key={rec.id}
                  className={`recommendation-card ${rec.category}`}
                >
                  <h6 className="recommendation-title">{rec.title}</h6>
                  <p className="recommendation-text">{rec.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Правая часть - Чат */}
          <div className="chat-panel">
            {error && (
              <Alert
                variant="danger"
                className="m-3"
                dismissible
                onClose={() => setError("")}
              >
                {error}
              </Alert>
            )}
            <div className="messages-container">
              {messages.map((message) => (
                <div key={message.id} className={`message ${message.sender}`}>
                  <div className={`message-content ${message.sender}`}>
                    <p>{message.text}</p>
                    <small className="message-time">
                      {message.timestamp.toLocaleTimeString("ru-RU", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </small>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="message ai">
                  <div className="message-content ai">
                    <Spinner animation="border" size="sm" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="input-container">
              <Form.Group className="mb-0">
                <div className="input-wrapper">
                  <Form.Control
                    type="text"
                    placeholder="Напишите ваш вопрос..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
                    disabled={isLoading}
                  />
                  <Button
                    variant="primary"
                    onClick={handleSendMessage}
                    disabled={isLoading || inputValue.trim() === ""}
                    className="send-button"
                  >
                    →
                  </Button>
                </div>
              </Form.Group>
            </div>
          </div>
        </div>
      </Modal.Body>
    </Modal>
  );
};

export default AIChatModal;
