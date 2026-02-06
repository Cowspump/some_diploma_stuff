import React, { useState, useEffect } from "react";
import {
  Container,
  Row,
  Col,
  Form,
  Button,
  Alert,
  Card,
  Badge,
} from "react-bootstrap";
import "../styles/App.css";

const MoodJournal = ({ isLoggedIn }) => {
  const [moodEntry, setMoodEntry] = useState("");
  const [currentMood, setCurrentMood] = useState("neutral");
  const [submitted, setSubmitted] = useState(false);
  const [entries, setEntries] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  const moodOptions = [
    { value: "very-bad", label: "😢", name: "Very Bad", score: 1 },
    { value: "bad", label: "😟", name: "Bad", score: 2 },
    { value: "neutral", label: "😐", name: "Neutral", score: 3 },
    { value: "good", label: "🙂", name: "Good", score: 4 },
    { value: "very-good", label: "😄", name: "Very Good", score: 5 },
  ];

  // Загрузка записей из localStorage при монтировании
  useEffect(() => {
    const savedEntries = localStorage.getItem("moodEntries");
    if (savedEntries) {
      setEntries(JSON.parse(savedEntries));
    }
  }, []);

  // Сохранение записей в localStorage при их изменении
  useEffect(() => {
    localStorage.setItem("moodEntries", JSON.stringify(entries));
  }, [entries]);

  const getMoodScore = (moodValue) => {
    return moodOptions.find((mood) => mood.value === moodValue)?.score || 0;
  };

  const getMoodName = (moodValue) => {
    return moodOptions.find((mood) => mood.value === moodValue)?.name || "";
  };

  const getMoodLabel = (moodValue) => {
    return moodOptions.find((mood) => mood.value === moodValue)?.label || "";
  };

  const calculateAverageMood = () => {
    if (entries.length === 0) return 0;
    const totalScore = entries.reduce(
      (sum, entry) => sum + getMoodScore(entry.mood),
      0,
    );
    return (totalScore / entries.length).toFixed(2);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (moodEntry.trim()) {
      const newEntry = {
        id: Date.now(),
        mood: currentMood,
        text: moodEntry,
        date: new Date().toLocaleDateString("ru-RU", {
          year: "numeric",
          month: "long",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        }),
      };
      setEntries([newEntry, ...entries]);
      setMoodEntry("");
      setCurrentMood("neutral");
      setSubmitted(true);
      setTimeout(() => setSubmitted(false), 3000);
    }
  };

  const deleteEntry = (id) => {
    setEntries(entries.filter((entry) => entry.id !== id));
  };

  const getAverageMoodLevel = () => {
    const avg = calculateAverageMood();
    if (avg >= 4.5) return { emoji: "😄", text: "Отлично!" };
    if (avg >= 3.5) return { emoji: "🙂", text: "Хорошо" };
    if (avg >= 2.5) return { emoji: "😐", text: "Нейтрально" };
    if (avg >= 1.5) return { emoji: "😟", text: "Плохо" };
    return { emoji: "😢", text: "Очень плохо" };
  };

  return (
    <section id="mood-journal" className="mood-journal-section py-5">
      <Container>
        <h2 className="section-title text-center mb-5">Mood Journal</h2>
        <Row>
          <Col lg={8} className="mx-auto">
            {!isLoggedIn ? (
              <Alert variant="info" className="text-center border-0">
                <p className="mb-0">
                  Please log in to write mood entries and track your emotional
                  journey.
                </p>
              </Alert>
            ) : (
              <>
                <div className="journal-form fade-in-animation mb-4">
                  <Form onSubmit={handleSubmit}>
                    <Form.Group className="mb-4">
                      <Form.Label className="mb-3 fs-6 fw-500">
                        How are you feeling today?
                      </Form.Label>
                      <div className="mood-selector d-flex justify-content-center gap-3">
                        {moodOptions.map((mood) => (
                          <button
                            key={mood.value}
                            type="button"
                            className={`mood-btn ${currentMood === mood.value ? "active" : ""}`}
                            onClick={() => setCurrentMood(mood.value)}
                            title={mood.name}
                          >
                            {mood.label}
                          </button>
                        ))}
                      </div>
                    </Form.Group>

                    <Form.Group className="mb-4">
                      <Form.Label htmlFor="moodText" className="mb-2">
                        Share your thoughts
                      </Form.Label>
                      <Form.Control
                        id="moodText"
                        as="textarea"
                        rows={5}
                        placeholder="Write about your day, feelings, or anything on your mind..."
                        value={moodEntry}
                        onChange={(e) => setMoodEntry(e.target.value)}
                        className="journal-textarea"
                      />
                    </Form.Group>

                    <div className="text-center">
                      <Button
                        type="submit"
                        className="btn-primary-custom"
                        disabled={!moodEntry.trim()}
                      >
                        Save Entry
                      </Button>
                    </div>
                  </Form>

                  {submitted && (
                    <Alert variant="success" className="mt-4 border-0">
                      ✓ Your mood entry has been saved successfully!
                    </Alert>
                  )}
                </div>

                {/* Статистика и кнопка просмотра истории */}
                {entries.length > 0 && (
                  <div className="mood-stats mb-4">
                    <Card className="border-0 shadow-sm">
                      <Card.Body>
                        <Row className="align-items-center">
                          <Col md={6}>
                            <h5 className="mb-0">Average Mood Level</h5>
                            <div className="mt-2">
                              <span className="fs-4">
                                {getAverageMoodLevel().emoji}
                              </span>
                              <span className="ms-2 fs-5">
                                {calculateAverageMood()}/5.0 -{" "}
                                {getAverageMoodLevel().text}
                              </span>
                            </div>
                          </Col>
                          <Col md={6} className="text-end">
                            <Button
                              variant={showHistory ? "secondary" : "primary"}
                              onClick={() => setShowHistory(!showHistory)}
                              size="sm"
                            >
                              {showHistory ? "Hide History" : "View History"} (
                              {entries.length})
                            </Button>
                          </Col>
                        </Row>
                      </Card.Body>
                    </Card>
                  </div>
                )}

                {/* История записей */}
                {showHistory && entries.length > 0 && (
                  <div className="history-section">
                    <h5 className="mb-3">Mood Entries History</h5>
                    {entries.map((entry) => (
                      <Card key={entry.id} className="mb-3 border-0 shadow-sm">
                        <Card.Body>
                          <div className="d-flex justify-content-between align-items-start">
                            <div className="flex-grow-1">
                              <div className="d-flex align-items-center gap-2 mb-2">
                                <span className="fs-5">
                                  {getMoodLabel(entry.mood)}
                                </span>
                                <Badge bg="info">
                                  {getMoodName(entry.mood)}
                                </Badge>
                                <small className="text-muted">
                                  {entry.date}
                                </small>
                              </div>
                              <p className="mb-0 text-break">{entry.text}</p>
                            </div>
                            <Button
                              variant="outline-danger"
                              size="sm"
                              onClick={() => deleteEntry(entry.id)}
                              className="ms-2"
                            >
                              ✕
                            </Button>
                          </div>
                        </Card.Body>
                      </Card>
                    ))}
                  </div>
                )}
              </>
            )}
          </Col>
        </Row>
      </Container>
    </section>
  );
};

export default MoodJournal;
