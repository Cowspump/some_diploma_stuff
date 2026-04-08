import React, { useState, useRef, useEffect } from "react";
import { Modal, Form, Button, Spinner, Alert } from "react-bootstrap";
import { useLanguage } from "../contexts/LanguageContext";
import { apiService } from "../services/api";
import { getAIChatHistory } from "../services/aiService";
import { getLocale } from "../i18n/locale";
import "../styles/AIChatModal.css";

const AIChatModal = ({ show, onHide, journalHistory: initialJournalHistory, testResults: initialTestResults }) => {
  const { t, lang } = useLanguage();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [journalHistory, setJournalHistory] = useState(initialJournalHistory || []);
  const [testResults, setTestResults] = useState(initialTestResults || []);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  useEffect(() => { scrollToBottom(); }, [messages]);

  useEffect(() => {
    if (show) {
      // Load persisted chat first; fall back to greeting if empty
      loadChatHistory();
      if (!initialJournalHistory || initialJournalHistory.length === 0) loadData();
      else { setJournalHistory(initialJournalHistory || []); setTestResults(initialTestResults || []); }
    }
  }, [show]);

  const loadChatHistory = async () => {
    try {
      const history = await getAIChatHistory(80);
      if (!history || history.length === 0) {
        setMessages([{ id: 1, text: t("ai_greeting"), sender: "ai", timestamp: new Date() }]);
        return;
      }

      const restored = [];
      for (const item of history) {
        const ts = item.created_at ? new Date(item.created_at) : new Date();
        restored.push({ id: `u-${item.id}`, text: item.request || "", sender: "user", timestamp: ts });
        restored.push({ id: `a-${item.id}`, text: item.response || "", sender: "ai", timestamp: ts });
      }
      setMessages(restored);
    } catch (err) {
      // If history can't be loaded, still allow chatting
      setMessages([{ id: 1, text: t("ai_greeting"), sender: "ai", timestamp: new Date() }]);
    }
  };

  const loadData = async () => {
    try {
      const journalRes = await apiService.get("/journal");
      setJournalHistory(journalRes.journals || []);
      const testsRes = await apiService.get("/test/results");
      setTestResults(testsRes.results || []);
    } catch (err) { console.error("Error loading data:", err); }
  };

  const generateRecommendations = () => {
    const recs = [];
    if (testResults && testResults.length > 0) {
      const avg = testResults.reduce((s, t) => s + (t.total_score || 0), 0) / testResults.length;
      if (avg < 50) recs.push({ id: 1, title: t("ai_stress"), description: t("ai_stress_desc"), category: "urgency" });
      recs.push({ id: 2, title: t("ai_trend"), description: `${avg.toFixed(1)}. ${testResults.length > 1 ? "✅" : ""}`, category: "analytics" });
    }
    if (journalHistory && journalHistory.length > 0) {
      if (journalHistory.some((e) => (e.wellbeing_score || 0) <= 2))
        recs.push({ id: 3, title: t("ai_mental"), description: t("ai_mental_desc"), category: "wellness" });
      recs.push({ id: 4, title: t("ai_last_entry"), description: `"${journalHistory[0]?.note_text?.substring(0, 50) || ""}..."`, category: "journal" });
    }
    if (recs.length === 0) recs.push({ id: 5, title: t("ai_start"), description: t("ai_start_desc"), category: "general" });
    return recs;
  };

  const handleSendMessage = async () => {
    if (inputValue.trim() === "") return;
    const text = inputValue;
    const userMsg = { id: Date.now(), text, sender: "user", timestamp: new Date() };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInputValue("");
    setIsLoading(true);
    setError("");

    // Build chat history for backend (exclude greeting, only user/ai pairs)
    const chatHistory = updatedMessages
      .filter(m => m.sender === "user" || m.sender === "ai")
      .map(m => ({ role: m.sender === "user" ? "user" : "ai", text: m.text }));

    try {
      const response = await apiService.post("/ai/ask", {
        prompt: text,
        chat_history: chatHistory,
      });
      setMessages((prev) => [...prev, {
        id: Date.now() + 1,
        text: response.response || "",
        sender: "ai",
        timestamp: new Date(),
      }]);
    } catch {
      setError(t("ai_error"));
      setMessages((prev) => [...prev, {
        id: Date.now() + 1,
        text: t("ai_error_msg"),
        sender: "ai",
        timestamp: new Date(),
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal show={show} onHide={onHide} size="xl" className="ai-chat-modal">
      <Modal.Header closeButton><Modal.Title>{t("ai_chat_title")}</Modal.Title></Modal.Header>
      <Modal.Body className="ai-chat-body p-0">
        <div className="chat-container">
          <div className="recommendations-panel">
            <div className="recommendations-header">
              <h5>{t("ai_recommendations")}</h5>
              <small className="text-muted">{t("ai_recommendations_sub")}</small>
            </div>
            <div className="recommendations-list">
              {generateRecommendations().map((rec) => (
                <div key={rec.id} className={`recommendation-card ${rec.category}`}>
                  <h6 className="recommendation-title">{rec.title}</h6>
                  <p className="recommendation-text">{rec.description}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="chat-panel">
            {error && <Alert variant="danger" className="m-3" dismissible onClose={() => setError("")}>{error}</Alert>}
            <div className="messages-container">
              {messages.map((msg) => (
                <div key={msg.id} className={`message ${msg.sender}`}>
                  <div className={`message-content ${msg.sender}`}>
                    <p>{msg.text}</p>
                    <small className="message-time">
                      {msg.timestamp.toLocaleTimeString(getLocale(lang), { hour: "2-digit", minute: "2-digit" })}
                    </small>
                  </div>
                </div>
              ))}
              {isLoading && <div className="message ai"><div className="message-content ai"><Spinner animation="border" size="sm" /></div></div>}
              <div ref={messagesEndRef} />
            </div>
            <div className="input-container">
              <Form.Group className="mb-0">
                <div className="input-wrapper">
                  <Form.Control type="text" placeholder={t("ai_placeholder")} value={inputValue} onChange={(e) => setInputValue(e.target.value)} onKeyPress={(e) => e.key === "Enter" && handleSendMessage()} disabled={isLoading} />
                  <Button variant="primary" onClick={handleSendMessage} disabled={isLoading || inputValue.trim() === ""} className="send-button">&rarr;</Button>
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
