import React, { useState, useEffect } from "react";
import {
  Container, Row, Col, Button, Nav, Navbar, Modal, Form, Alert, Badge, Dropdown,
} from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/LanguageContext";
import { addQuestion, deleteQuestion, fetchTestQuestions, createTest, getTests, deleteTest } from "../services/testService";
import { apiService } from "../services/api";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { getLocale } from "../i18n/locale";
import "../styles/Dashboard.css";

const TherapistDashboard = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const { t, lang, switchLang } = useLanguage();
  const [activeView, setActiveView] = useState("tests");
  const [tests, setTests] = useState([]);
  const [selectedTest, setSelectedTest] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [showAddTestModal, setShowAddTestModal] = useState(false);
  const [showAddQuestionModal, setShowAddQuestionModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [newTest, setNewTest] = useState({ title: "", description: "" });
  const [newQuestion, setNewQuestion] = useState({ text: "", options: [{ text: "", points: 0 }, { text: "", points: 0 }] });

  // Users state
  const [workers, setWorkers] = useState([]);
  const [selectedWorker, setSelectedWorker] = useState(null);
  const [workersLoading, setWorkersLoading] = useState(false);

  useEffect(() => { loadTests(); }, [lang]);
  useEffect(() => {
    if (selectedTest) loadQuestions(selectedTest.id);
    else setQuestions([]);
  }, [selectedTest]);

  useEffect(() => {
    if (activeView === "users") loadWorkers();
  }, [activeView]);

  const loadTests = async () => {
    setLoading(true);
    try { setTests(await getTests(lang)); } catch { setError(t("therapist_load_tests_error")); } finally { setLoading(false); }
  };

  const loadQuestions = async (testId) => {
    setLoading(true);
    try { setQuestions(await fetchTestQuestions(testId, lang)); } catch { setError(t("therapist_load_questions_error")); } finally { setLoading(false); }
  };

  const loadWorkers = async () => {
    setWorkersLoading(true);
    try {
      const data = await apiService.get("/therapist/workers");
      setWorkers(data.workers || []);
    } catch {
      setError(t("therapist_users_load_error"));
    } finally {
      setWorkersLoading(false);
    }
  };

  const handleDeleteWorker = async (worker) => {
    if (!worker?.id) return;
    if (!window.confirm(t("therapist_confirm_delete_user"))) return;
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      await apiService.delete(`/admin/user/${worker.id}`);
      setSuccess(t("therapist_user_deleted"));
      setSelectedWorker(null);
      await loadWorkers();
    } catch (err) {
      setError(err?.message || "Error");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => { onLogout(); navigate("/"); };

  const handleCreateTest = async (e) => {
    e.preventDefault();
    if (!newTest.title.trim()) { setError(t("therapist_err_title")); return; }
    setLoading(true);
    try {
      await createTest(newTest);
      setSuccess(t("therapist_test_created"));
      setShowAddTestModal(false);
      setNewTest({ title: "", description: "" });
      await loadTests();
    } catch (err) { setError(err.message || "Error"); } finally { setLoading(false); }
  };

  const handleDeleteTest = async (testId) => {
    if (!window.confirm(t("therapist_confirm_delete_test"))) return;
    setLoading(true);
    try {
      await deleteTest(testId);
      setSuccess(t("therapist_test_deleted"));
      if (selectedTest?.id === testId) setSelectedTest(null);
      await loadTests();
    } catch (err) { setError(err.message || "Error"); } finally { setLoading(false); }
  };

  const handleOptionChange = (index, field, value) => {
    const opts = [...newQuestion.options];
    opts[index][field] = field === "points" ? parseInt(value) || 0 : value;
    setNewQuestion({ ...newQuestion, options: opts });
  };

  const handleSubmitQuestion = async (e) => {
    e.preventDefault();
    setError("");
    if (!newQuestion.text.trim()) { setError(t("therapist_err_q_text")); return; }
    if (newQuestion.options.length < 2) { setError(t("therapist_err_min_options")); return; }
    for (const o of newQuestion.options) if (!o.text.trim()) { setError(t("therapist_err_fill_options")); return; }
    setLoading(true);
    try {
      await addQuestion({ ...newQuestion, test_id: selectedTest?.id || null });
      setSuccess(t("therapist_q_added"));
      setShowAddQuestionModal(false);
      setNewQuestion({ text: "", options: [{ text: "", points: 0 }, { text: "", points: 0 }] });
      if (selectedTest) await loadQuestions(selectedTest.id);
      await loadTests();
    } catch (err) { setError(err.message || "Error"); } finally { setLoading(false); }
  };

  const handleDeleteQuestion = async (qId) => {
    if (!window.confirm(t("therapist_confirm_delete_q"))) return;
    setLoading(true);
    try {
      await deleteQuestion(qId);
      setSuccess(t("therapist_q_deleted"));
      if (selectedTest) await loadQuestions(selectedTest.id);
      await loadTests();
    } catch (err) { setError(err.message || "Error"); } finally { setLoading(false); }
  };

  const totalQuestions = tests.reduce((s, t) => s + (t.question_count || 0), 0);

  const getScoreBadge = (score) => {
    if (score >= 80) return <Badge bg="success">{t("results_excellent")}</Badge>;
    if (score >= 60) return <Badge bg="primary">{t("results_good")}</Badge>;
    if (score >= 40) return <Badge bg="warning">{t("results_average")}</Badge>;
    return <Badge bg="danger">{t("results_attention")}</Badge>;
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString(getLocale(lang), {
      day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit"
    });
  };

  const computeMoodTrend = (journalScores = []) => {
    if (!Array.isArray(journalScores) || journalScores.length < 2) return null;
    const sorted = [...journalScores].sort((a, b) => new Date(a.date) - new Date(b.date));
    const first = sorted[0]?.score;
    const last = sorted[sorted.length - 1]?.score;
    if (typeof first !== "number" || typeof last !== "number") return null;
    const delta = last - first;
    return { delta, first, last };
  };

  const buildWorkerAnalytics = (worker) => {
    const testSeries = (worker?.test_results || [])
      .slice()
      .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
      .map((r) => ({
        name: new Date(r.created_at).toLocaleDateString(getLocale(lang), { day: "2-digit", month: "short" }),
        score: r.total_score,
      }));

    const moodSeries = (worker?.journal_scores || [])
      .slice()
      .sort((a, b) => new Date(a.date) - new Date(b.date))
      .map((j) => ({
        day: new Date(j.date).toLocaleDateString(getLocale(lang), { weekday: "short" }),
        mood: j.score,
      }));

    // Burnout risk score (same logic as BurnoutScale)
    let riskScore = 50;
    if (testSeries.length > 0) {
      const avgTest = testSeries.reduce((s, r) => s + (r.score || 0), 0) / testSeries.length;
      riskScore = Math.max(0, 100 - avgTest);
    }
    if (moodSeries.length > 0) {
      const avgMood = moodSeries.reduce((s, j) => s + (j.mood || 0), 0) / moodSeries.length;
      const moodRisk = ((5 - avgMood) / 5) * 100;
      riskScore = Math.round((riskScore + moodRisk) / 2);
    }
    const burnout = Math.min(100, Math.max(0, riskScore));

    return { testSeries, moodSeries, burnout };
  };

  const getBurnoutLabel = (level) => {
    if (level >= 70) return t("burnout_high");
    if (level >= 40) return t("burnout_medium");
    return t("burnout_low");
  };

  const getBurnoutColor = (level) => {
    if (level >= 70) return "#dc3545";
    if (level >= 40) return "#ffc107";
    return "#28a745";
  };

  return (
    <div className="dashboard">
      {/* Navbar */}
      <Navbar className="navbar-custom shadow" sticky="top">
        <Container>
          <Navbar.Brand>{t("therapist_title")}</Navbar.Brand>
          <Nav className="ms-auto">
            <div className="user-info">
              <Dropdown>
                <Dropdown.Toggle variant="outline-secondary" size="sm" className="lang-toggle">
                  {lang === "ru" ? "RU" : lang === "en" ? "EN" : "中文"}
                </Dropdown.Toggle>
                <Dropdown.Menu>
                  <Dropdown.Item onClick={() => switchLang("ru")}>Русский</Dropdown.Item>
                  <Dropdown.Item onClick={() => switchLang("zh")}>中文</Dropdown.Item>
                  <Dropdown.Item onClick={() => switchLang("en")}>English</Dropdown.Item>
                </Dropdown.Menu>
              </Dropdown>
              <span>{t("therapist_welcome")} {user?.fullName || user?.email}!</span>
              <Button variant="outline-danger" size="sm" className="logout-btn" onClick={handleLogout}>
                {t("nav_logout")}
              </Button>
            </div>
          </Nav>
        </Container>
      </Navbar>

      <Container className="content-area">
        {error && <Alert variant="danger" dismissible onClose={() => setError("")}>{error}</Alert>}
        {success && <Alert variant="success" dismissible onClose={() => setSuccess("")}>{success}</Alert>}

        {/* Dashboard Tabs */}
        <div className="dashboard-tabs">
          <button className={`dashboard-tab ${activeView === "tests" ? "active" : ""}`} onClick={() => setActiveView("tests")}>
            {t("therapist_tab_tests")}
          </button>
          <button className={`dashboard-tab ${activeView === "users" ? "active" : ""}`} onClick={() => setActiveView("users")}>
            {t("therapist_tab_users")}
          </button>
        </div>

        {activeView === "tests" && (
          <>
            {/* Stats Row */}
            <div className="stats-row">
              <div className="stat-card">
                <div className="stat-icon purple">📋</div>
                <div>
                  <div className="stat-value">{tests.length}</div>
                  <div className="stat-label">{t("therapist_tests")}</div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon green">❓</div>
                <div>
                  <div className="stat-value">{totalQuestions}</div>
                  <div className="stat-label">{t("therapist_q_text")}</div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon blue">📊</div>
                <div>
                  <div className="stat-value">{selectedTest?.question_count || 0}</div>
                  <div className="stat-label">{selectedTest ? selectedTest.title : "—"}</div>
                </div>
              </div>
            </div>

            {/* Scoring Guide */}
            <div className="scoring-guide">
              <h6>{t("therapist_scoring_guide")}</h6>
              <p style={{ fontSize: "0.875rem", color: "#a1a1b5", marginBottom: "0.5rem" }}>{t("therapist_scoring_desc")}</p>
              <ul>
                <li>🟢 {t("therapist_scoring_high")}</li>
                <li>🟡 {t("therapist_scoring_mid")}</li>
                <li>🔴 {t("therapist_scoring_low")}</li>
              </ul>
              <div className="scoring-tip">💡 {t("therapist_scoring_tip")}</div>
            </div>

            <Row className="g-4">
              {/* Left Panel - Tests */}
              <Col lg={4}>
                <div className="test-list-panel">
                  <div className="test-list-header">
                    <h5>{t("therapist_tests")}</h5>
                    <Button className="btn-add" size="sm" onClick={() => setShowAddTestModal(true)}>
                      {t("therapist_new_test")}
                    </Button>
                  </div>
                  <div className="test-list-body">
                    {tests.length === 0 ? (
                      <div className="empty-state">
                        <div className="empty-state-icon">📋</div>
                        <h5>{t("therapist_no_tests")}</h5>
                        <p>{t("therapist_or_create")}</p>
                      </div>
                    ) : (
                      tests.map((test) => (
                        <div
                          key={test.id}
                          className={`test-item ${selectedTest?.id === test.id ? "active" : ""}`}
                          onClick={() => setSelectedTest(test)}
                        >
                          <div className="test-item-info">
                            <h6>{test.title}</h6>
                            <div className="test-meta">
                              <span className="question-count">{test.question_count} {t("therapist_questions")}</span>
                              {test.description && <span>{test.description.substring(0, 30)}...</span>}
                            </div>
                          </div>
                          <Button
                            variant="outline-danger"
                            size="sm"
                            className="delete-btn"
                            onClick={(e) => { e.stopPropagation(); handleDeleteTest(test.id); }}
                          >
                            &times;
                          </Button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </Col>

              {/* Right Panel - Questions */}
              <Col lg={8}>
                <div className="questions-panel">
                  {selectedTest ? (
                    <>
                      <div className="questions-header">
                        <div>
                          <h5>{selectedTest.title}</h5>
                          {selectedTest.description && <p>{selectedTest.description}</p>}
                        </div>
                        <Button className="btn-gradient" size="sm" onClick={() => setShowAddQuestionModal(true)}>
                          {t("therapist_add_question")}
                        </Button>
                      </div>
                      <div className="questions-body">
                        {questions.length === 0 ? (
                          <div className="empty-state">
                            <div className="empty-state-icon">❓</div>
                            <h5>{t("therapist_no_questions")}</h5>
                          </div>
                        ) : (
                          questions.map((q, i) => (
                            <div key={q.id} className="question-card">
                              <div className="d-flex align-items-start">
                                <span className="question-number">{i + 1}</span>
                                <div className="flex-grow-1">
                                  <div className="question-text">{q.text}</div>
                                  <div className="option-list">
                                    {q.options.map((opt, oi) => (
                                      <span key={oi} className="option-chip">
                                        {opt.text}
                                        <span className="points-badge">{opt.points}</span>
                                      </span>
                                    ))}
                                  </div>
                                </div>
                                <Button
                                  variant="outline-danger"
                                  size="sm"
                                  className="ms-3"
                                  onClick={() => handleDeleteQuestion(q.id)}
                                  disabled={loading}
                                >
                                  &times;
                                </Button>
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </>
                  ) : (
                    <div className="empty-state">
                      <div className="empty-state-icon">👈</div>
                      <h5>{t("therapist_select_test")}</h5>
                      <p>{t("therapist_or_create")}</p>
                    </div>
                  )}
                </div>
              </Col>
            </Row>
          </>
        )}

        {activeView === "users" && (
          <>
            {/* Stats Row for users */}
            <div className="stats-row">
              <div className="stat-card">
                <div className="stat-icon purple">👥</div>
                <div>
                  <div className="stat-value">{workers.length}</div>
                  <div className="stat-label">{t("therapist_users_count")}</div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon green">📊</div>
                <div>
                  <div className="stat-value">{workers.reduce((s, w) => s + w.test_results.length, 0)}</div>
                  <div className="stat-label">{t("therapist_user_tests_count")}</div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon pink">📓</div>
                <div>
                  <div className="stat-value">{workers.reduce((s, w) => s + w.journals_count, 0)}</div>
                  <div className="stat-label">{t("therapist_user_journals")}</div>
                </div>
              </div>
            </div>

            <Row className="g-4">
              {/* Left - Users list */}
              <Col lg={4}>
                <div className="users-panel">
                  <div className="users-panel-header">
                    <h5>{t("therapist_users_title")}</h5>
                    <Button className="btn-add" size="sm" onClick={loadWorkers} style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.15)", color: "#a1a1b5" }}>
                      {t("results_refresh")}
                    </Button>
                  </div>
                  {workersLoading ? (
                    <div className="empty-state">
                      <div className="spinner-border spinner-border-sm" role="status" />
                    </div>
                  ) : workers.length === 0 ? (
                    <div className="empty-state">
                      <div className="empty-state-icon">👥</div>
                      <h5>{t("therapist_no_workers")}</h5>
                    </div>
                  ) : (
                    workers.map((w) => (
                      <div
                        key={w.id}
                        className={`user-card d-flex align-items-center gap-3 ${selectedWorker?.id === w.id ? "active" : ""}`}
                        onClick={() => setSelectedWorker(w)}
                      >
                        <div className="user-avatar">
                          {w.full_name.charAt(0).toUpperCase()}
                        </div>
                        <div className="user-card-info flex-grow-1">
                          <h6>{w.full_name}</h6>
                          <small>{w.mail}</small>
                        </div>
                        <div className="text-end">
                          <div style={{ color: "#a29bfe", fontWeight: 700, fontSize: "1.1rem" }}>
                            {w.test_results.length}
                          </div>
                          <small style={{ color: "#6b6b80", fontSize: "0.7rem" }}>{t("therapist_tests")}</small>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </Col>

              {/* Right - User results */}
              <Col lg={8}>
                <div className="user-results-panel">
                  {selectedWorker ? (
                    <>
                      <div className="results-header">
                        <div className="d-flex align-items-center gap-3 mb-2">
                          <div className="user-avatar" style={{ width: 48, height: 48, fontSize: "1.2rem" }}>
                            {selectedWorker.full_name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <h5>{selectedWorker.full_name}</h5>
                            <p className="mb-0">{selectedWorker.mail}</p>
                          </div>
                        </div>
                        <div className="d-flex justify-content-between align-items-center">
                          <div className="d-flex gap-3 mt-2">
                            <span style={{ color: "#a1a1b5", fontSize: "0.85rem" }}>
                              {t("therapist_user_avg")}: <strong style={{ color: "#a29bfe" }}>{selectedWorker.avg_score ?? "—"}</strong>
                            </span>
                            <span style={{ color: "#a1a1b5", fontSize: "0.85rem" }}>
                              {t("therapist_user_journals")}: <strong style={{ color: "#00cec9" }}>{selectedWorker.journals_count}</strong>
                            </span>
                          </div>
                          <Button
                            variant="outline-danger"
                            size="sm"
                            onClick={() => handleDeleteWorker(selectedWorker)}
                            disabled={loading}
                          >
                            {t("therapist_delete_user")}
                          </Button>
                        </div>
                        <div className="d-flex gap-3 mt-2">
                          {/* spacing kept for layout; detailed analytics below */}
                        </div>
                      </div>

                      {/* Extended analytics */}
                      <div className="mb-3">
                        <h6 className="mb-2">{t("therapist_user_mood")}</h6>
                        {Array.isArray(selectedWorker.journal_scores) && selectedWorker.journal_scores.length > 0 ? (
                          <>
                            <div style={{ color: "#a1a1b5", fontSize: "0.85rem" }} className="mb-2">
                              {(() => {
                                const trend = computeMoodTrend(selectedWorker.journal_scores);
                                if (!trend) return "—";
                                const arrow = trend.delta > 0 ? "↑" : trend.delta < 0 ? "↓" : "→";
                                return `${t("therapist_user_mood_trend")}: ${arrow} (${trend.first} → ${trend.last}, Δ ${trend.delta})`;
                              })()}
                            </div>
                            <div style={{ maxHeight: 160, overflow: "auto", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 12, padding: 12 }}>
                              {[...selectedWorker.journal_scores]
                                .sort((a, b) => new Date(b.date) - new Date(a.date))
                                .slice(0, 14)
                                .map((js, idx) => (
                                  <div key={`${js.date}-${idx}`} className="d-flex justify-content-between" style={{ padding: "4px 0", borderBottom: "1px dashed rgba(255,255,255,0.06)" }}>
                                    <span style={{ color: "#a1a1b5", fontSize: "0.85rem" }}>{formatDate(js.date)}</span>
                                    <strong style={{ color: "#00cec9" }}>{js.score}/5</strong>
                                  </div>
                                ))}
                            </div>
                          </>
                        ) : (
                          <div className="text-muted" style={{ fontSize: "0.9rem" }}>{t("analytics_no_mood")}</div>
                        )}
                      </div>

                      {/* Analytics like main page (charts + burnout) */}
                      {(() => {
                        const { testSeries, moodSeries, burnout } = buildWorkerAnalytics(selectedWorker);
                        const noData = testSeries.length === 0 && moodSeries.length === 0;
                        if (noData) return null;
                        return (
                          <div className="mb-4">
                            <Row className="g-3">
                              <Col lg={6}>
                                <div className="analytics-card p-3" style={{ borderRadius: 14 }}>
                                  <h6 className="mb-3">{t("analytics_tests")}</h6>
                                  {testSeries.length === 0 ? (
                                    <div className="text-muted">{t("analytics_no_tests")}</div>
                                  ) : (
                                    <ResponsiveContainer width="100%" height={240}>
                                      <LineChart data={testSeries}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                                        <XAxis dataKey="name" stroke="#999" />
                                        <YAxis stroke="#999" />
                                        <Tooltip contentStyle={{ backgroundColor: "#fff", border: "1px solid #ddd", borderRadius: "8px" }} />
                                        <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={3} dot={{ fill: "#6366f1", r: 4 }} activeDot={{ r: 6 }} />
                                      </LineChart>
                                    </ResponsiveContainer>
                                  )}
                                </div>
                              </Col>
                              <Col lg={6}>
                                <div className="analytics-card p-3" style={{ borderRadius: 14 }}>
                                  <h6 className="mb-3">{t("analytics_mood")}</h6>
                                  {moodSeries.length === 0 ? (
                                    <div className="text-muted">{t("analytics_no_mood")}</div>
                                  ) : (
                                    <ResponsiveContainer width="100%" height={240}>
                                      <BarChart data={moodSeries}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                                        <XAxis dataKey="day" stroke="#999" />
                                        <YAxis stroke="#999" domain={[0, 5]} />
                                        <Tooltip contentStyle={{ backgroundColor: "#fff", border: "1px solid #ddd", borderRadius: "8px" }} />
                                        <Bar dataKey="mood" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
                                      </BarChart>
                                    </ResponsiveContainer>
                                  )}
                                </div>
                              </Col>
                            </Row>

                            <div className="mt-3 analytics-card p-3" style={{ borderRadius: 14 }}>
                              <div className="d-flex justify-content-between align-items-center mb-2">
                                <h6 className="mb-0">{t("burnout_title")}</h6>
                                <strong style={{ color: getBurnoutColor(burnout) }}>{burnout}%</strong>
                              </div>
                              <div style={{ height: 10, borderRadius: 999, background: "#e5e7eb", overflow: "hidden" }}>
                                <div style={{ width: `${burnout}%`, height: "100%", background: getBurnoutColor(burnout) }} />
                              </div>
                              <div className="text-muted mt-2" style={{ fontSize: "0.9rem" }}>
                                {getBurnoutLabel(burnout)}
                              </div>
                            </div>
                          </div>
                        );
                      })()}

                      <div className="mb-4">
                        <h6 className="mb-2">{t("therapist_user_ai_summary")}</h6>
                        {selectedWorker.ai_summary ? (
                          <div style={{ whiteSpace: "pre-wrap", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 12, padding: 12 }}>
                            {selectedWorker.ai_summary}
                          </div>
                        ) : (
                          <div className="text-muted" style={{ fontSize: "0.9rem" }}>{t("therapist_user_no_summary")}</div>
                        )}
                      </div>

                      <div>
                        {selectedWorker.test_results.length === 0 ? (
                          <div className="empty-state">
                            <div className="empty-state-icon">📋</div>
                            <h5>{t("therapist_user_no_results")}</h5>
                          </div>
                        ) : (
                          selectedWorker.test_results.map((r) => (
                            <div key={r.id} className="result-item">
                              <div>
                                <div className="result-test-name">{r.test_title || `Test #${r.test_id || "?"}`}</div>
                                <div className="result-date">{formatDate(r.created_at)}</div>
                              </div>
                              <div className="d-flex align-items-center gap-2">
                                <span className="result-score">{r.total_score}</span>
                                {getScoreBadge(r.total_score)}
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </>
                  ) : (
                    <div className="empty-state">
                      <div className="empty-state-icon">👈</div>
                      <h5>{t("therapist_select_user")}</h5>
                      <p>{t("therapist_select_user_desc")}</p>
                    </div>
                  )}
                </div>
              </Col>
            </Row>
          </>
        )}
      </Container>

      {/* Create Test Modal */}
      <Modal show={showAddTestModal} onHide={() => setShowAddTestModal(false)} centered>
        <Modal.Header closeButton><Modal.Title>{t("therapist_new_test_title")}</Modal.Title></Modal.Header>
        <Modal.Body>
          <Form onSubmit={handleCreateTest}>
            <Form.Group className="mb-3">
              <Form.Label className="fw-semibold">{t("therapist_test_name")}</Form.Label>
              <Form.Control type="text" placeholder={t("therapist_test_name_placeholder")} value={newTest.title} onChange={(e) => setNewTest({ ...newTest, title: e.target.value })} style={{ borderRadius: "10px" }} />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label className="fw-semibold">{t("therapist_test_desc")}</Form.Label>
              <Form.Control as="textarea" rows={3} placeholder={t("therapist_test_desc_placeholder")} value={newTest.description} onChange={(e) => setNewTest({ ...newTest, description: e.target.value })} style={{ borderRadius: "10px" }} />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer style={{ borderTop: "none" }}>
          <Button variant="secondary" onClick={() => setShowAddTestModal(false)} style={{ borderRadius: "10px" }}>{t("therapist_cancel")}</Button>
          <Button className="btn-gradient" onClick={handleCreateTest} disabled={loading}>{loading ? t("therapist_creating") : t("therapist_create")}</Button>
        </Modal.Footer>
      </Modal>

      {/* Add Question Modal */}
      <Modal show={showAddQuestionModal} onHide={() => setShowAddQuestionModal(false)} size="lg" centered>
        <Modal.Header closeButton><Modal.Title>{t("therapist_add_q_title")} "{selectedTest?.title}"</Modal.Title></Modal.Header>
        <Modal.Body>
          <Form onSubmit={handleSubmitQuestion}>
            <Form.Group className="mb-3">
              <Form.Label className="fw-semibold">{t("therapist_q_text_label")}</Form.Label>
              <Form.Control type="text" placeholder={t("therapist_q_text_placeholder")} value={newQuestion.text} onChange={(e) => setNewQuestion({ ...newQuestion, text: e.target.value })} disabled={loading} style={{ borderRadius: "10px" }} />
            </Form.Group>
            <Form.Label className="fw-semibold">{t("therapist_options_label")}</Form.Label>
            <div className="mb-2" style={{ fontSize: "0.8rem", color: "#6b6b80" }}>
              {t("therapist_scoring_tip")}
            </div>
            {newQuestion.options.map((opt, i) => (
              <Row key={i} className="mb-2 align-items-center">
                <Col>
                  <Form.Control type="text" placeholder={t("therapist_option_placeholder")} value={opt.text} onChange={(e) => handleOptionChange(i, "text", e.target.value)} disabled={loading} style={{ borderRadius: "10px" }} />
                </Col>
                <Col xs={3}>
                  <Form.Control type="number" min="0" max="5" placeholder="0-5" value={opt.points} onChange={(e) => handleOptionChange(i, "points", e.target.value)} disabled={loading} style={{ borderRadius: "10px" }} />
                </Col>
                <Col xs={1}>
                  {newQuestion.options.length > 2 && (
                    <Button variant="outline-danger" size="sm" onClick={() => setNewQuestion({ ...newQuestion, options: newQuestion.options.filter((_, j) => j !== i) })} disabled={loading} style={{ borderRadius: "50%", width: "32px", height: "32px", padding: 0 }}>&times;</Button>
                  )}
                </Col>
              </Row>
            ))}
            <Button variant="outline-secondary" size="sm" onClick={() => setNewQuestion({ ...newQuestion, options: [...newQuestion.options, { text: "", points: 0 }] })} className="mt-2" disabled={loading} style={{ borderRadius: "10px" }}>
              {t("therapist_add_option")}
            </Button>
          </Form>
        </Modal.Body>
        <Modal.Footer style={{ borderTop: "none" }}>
          <Button variant="secondary" onClick={() => setShowAddQuestionModal(false)} disabled={loading} style={{ borderRadius: "10px" }}>{t("therapist_cancel")}</Button>
          <Button className="btn-gradient" onClick={handleSubmitQuestion} disabled={loading}>{loading ? t("therapist_saving") : t("therapist_save")}</Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default TherapistDashboard;
