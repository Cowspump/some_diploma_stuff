import React, { useState, useEffect } from "react";
import { Container, Row, Col, Form, Button, Alert, Card, Badge } from "react-bootstrap";
import { useLanguage } from "../contexts/LanguageContext";
import { apiService } from "../services/api";
import { getLocale } from "../i18n/locale";
import "../styles/App.css";

const MoodJournal = ({ isLoggedIn }) => {
  const { t, lang } = useLanguage();
  const [moodEntry, setMoodEntry] = useState("");
  const [currentMood, setCurrentMood] = useState(3);
  const [submitted, setSubmitted] = useState(false);
  const [entries, setEntries] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const moodOptions = [
    { value: 0, label: "😢", nameKey: "mood_very_bad" },
    { value: 1, label: "😟", nameKey: "mood_bad" },
    { value: 2, label: "😐", nameKey: "mood_neutral" },
    { value: 3, label: "🙂", nameKey: "mood_good" },
    { value: 4, label: "😄", nameKey: "mood_very_good" },
    { value: 5, label: "🤩", nameKey: "mood_excellent" },
  ];

  useEffect(() => {
    if (isLoggedIn) loadJournals();
  }, [isLoggedIn]);

  const loadJournals = async () => {
    try {
      const response = await apiService.get("/journal");
      setEntries(response.journals || []);
    } catch {
      setError(t("journal_load_error"));
    }
  };

  const getMoodName = (val) => {
    const m = moodOptions.find((o) => o.value === val);
    return m ? t(m.nameKey) : "";
  };

  const getMoodLabel = (val) => moodOptions.find((o) => o.value === val)?.label || "";

  const calculateAverageMood = () => {
    if (entries.length === 0) return 0;
    return (entries.reduce((s, e) => s + (e.wellbeing_score || 0), 0) / entries.length).toFixed(2);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!moodEntry.trim()) return;
    setLoading(true);
    setError("");
    try {
      await apiService.post("/journal", { score: currentMood, note: moodEntry });
      setMoodEntry("");
      setCurrentMood(3);
      setSubmitted(true);
      setTimeout(() => setSubmitted(false), 3000);
      await loadJournals();
    } catch {
      setError(t("journal_save_error"));
    } finally {
      setLoading(false);
    }
  };

  const deleteEntry = async (id) => {
    try {
      await apiService.delete(`/journal/${id}`);
      setEntries(entries.filter((e) => e.id !== id));
    } catch {
      setError(t("journal_delete_error"));
    }
  };

  const getAverageMoodLevel = () => {
    const avg = calculateAverageMood();
    if (avg >= 4.5) return { emoji: "😄", text: t("mood_excellent") };
    if (avg >= 3.5) return { emoji: "🙂", text: t("mood_good") };
    if (avg >= 2.5) return { emoji: "😐", text: t("mood_neutral") };
    if (avg >= 1.5) return { emoji: "😟", text: t("mood_bad") };
    return { emoji: "😢", text: t("mood_very_bad") };
  };

  return (
    <section id="mood-journal" className="mood-journal-section py-5">
      <Container>
        <h2 className="section-title text-center mb-5">{t("journal_title")}</h2>
        <Row>
          <Col lg={8} className="mx-auto">
            {!isLoggedIn ? (
              <Alert variant="info" className="text-center border-0"><p className="mb-0">{t("journal_login_msg")}</p></Alert>
            ) : (
              <>
                <div className="journal-form fade-in-animation mb-4">
                  <Form onSubmit={handleSubmit}>
                    <Form.Group className="mb-4">
                      <Form.Label className="mb-3 fs-6 fw-500">{t("journal_how_feeling")}</Form.Label>
                      <div className="mood-selector d-flex justify-content-center gap-3">
                        {moodOptions.map((mood) => (
                          <button key={mood.value} type="button" className={`mood-btn ${currentMood === mood.value ? "active" : ""}`} onClick={() => setCurrentMood(mood.value)} title={t(mood.nameKey)}>
                            {mood.label}
                          </button>
                        ))}
                      </div>
                    </Form.Group>
                    <Form.Group className="mb-4">
                      <Form.Label>{t("journal_share")}</Form.Label>
                      <Form.Control as="textarea" rows={5} placeholder={t("journal_placeholder")} value={moodEntry} onChange={(e) => setMoodEntry(e.target.value)} className="journal-textarea" />
                    </Form.Group>
                    <div className="text-center">
                      <Button type="submit" className="btn-primary-custom" disabled={!moodEntry.trim() || loading}>
                        {loading ? t("journal_saving") : t("journal_save")}
                      </Button>
                    </div>
                  </Form>
                  {error && <Alert variant="danger" className="mt-4 border-0">{error}</Alert>}
                  {submitted && <Alert variant="success" className="mt-4 border-0">✓ {t("journal_saved")}</Alert>}
                </div>

                {entries.length > 0 && (
                  <div className="mood-stats mb-4">
                    <Card className="border-0 shadow-sm">
                      <Card.Body>
                        <Row className="align-items-center">
                          <Col md={6}>
                            <h5 className="mb-0">{t("journal_avg")}</h5>
                            <div className="mt-2">
                              <span className="fs-4">{getAverageMoodLevel().emoji}</span>
                              <span className="ms-2 fs-5">{calculateAverageMood()}/5.0 - {getAverageMoodLevel().text}</span>
                            </div>
                          </Col>
                          <Col md={6} className="text-end">
                            <Button variant={showHistory ? "secondary" : "primary"} onClick={() => setShowHistory(!showHistory)} size="sm">
                              {showHistory ? t("journal_hide") : t("journal_show")} ({entries.length})
                            </Button>
                          </Col>
                        </Row>
                      </Card.Body>
                    </Card>
                  </div>
                )}

                {showHistory && entries.length > 0 && (
                  <div className="history-section">
                    <h5 className="mb-3">{t("journal_history")}</h5>
                    {entries.map((entry) => (
                      <Card key={entry.id} className="mb-3 border-0 shadow-sm">
                        <Card.Body>
                          <div className="d-flex justify-content-between align-items-start">
                            <div className="flex-grow-1">
                              <div className="d-flex align-items-center gap-2 mb-2">
                                <span className="fs-5">{getMoodLabel(entry.wellbeing_score)}</span>
                                <Badge bg="info">{getMoodName(entry.wellbeing_score)}</Badge>
                                <small className="text-muted">
                                  {new Date(entry.created_at).toLocaleDateString(getLocale(lang), {
                                    year: "numeric",
                                    month: "long",
                                    day: "numeric",
                                    hour: "2-digit",
                                    minute: "2-digit",
                                  })}
                                </small>
                              </div>
                              <p className="mb-0 text-break">{entry.note_text || ""}</p>
                            </div>
                            <Button variant="outline-danger" size="sm" onClick={() => deleteEntry(entry.id)} className="ms-2">&times;</Button>
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
