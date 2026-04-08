import React, { useState, useEffect } from "react";
import {
  Container, Row, Col, Button, Nav, Navbar, Modal, Form, Alert, Badge, Dropdown,
} from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/LanguageContext";
import { addQuestion, deleteQuestion, fetchTestQuestions, createTest, getTests, deleteTest } from "../services/testService";
import { apiService } from "../services/api";
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

  useEffect(() => { loadTests(); }, []);
  useEffect(() => {
    if (selectedTest) loadQuestions(selectedTest.id);
    else setQuestions([]);
  }, [selectedTest]);

  useEffect(() => {
    if (activeView === "users") loadWorkers();
  }, [activeView]);

  const loadTests = async () => {
    setLoading(true);
    try { setTests(await getTests()); } catch { setError("Error loading tests"); } finally { setLoading(false); }
  };

  const loadQuestions = async (testId) => {
    setLoading(true);
    try { setQuestions(await fetchTestQuestions(testId)); } catch { setError("Error loading questions"); } finally { setLoading(false); }
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
    if (score >= 80) return <Badge bg="success">Excellent</Badge>;
    if (score >= 60) return <Badge bg="primary">Good</Badge>;
    if (score >= 40) return <Badge bg="warning">Average</Badge>;
    return <Badge bg="danger">Attention</Badge>;
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString(lang === "ru" ? "ru-RU" : "zh-CN", {
      day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit"
    });
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
                <Dropdown.Toggle variant="outline-light" size="sm">{lang === "ru" ? "RU" : "中文"}</Dropdown.Toggle>
                <Dropdown.Menu>
                  <Dropdown.Item onClick={() => switchLang("ru")}>Русский</Dropdown.Item>
                  <Dropdown.Item onClick={() => switchLang("zh")}>中文</Dropdown.Item>
                </Dropdown.Menu>
              </Dropdown>
              <span>{t("therapist_welcome")} {user?.fullName || user?.email}!</span>
              <Button variant="outline-light" size="sm" onClick={handleLogout}>{t("nav_logout")}</Button>
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
                        <div className="d-flex gap-3 mt-2">
                          <span style={{ color: "#a1a1b5", fontSize: "0.85rem" }}>
                            {t("therapist_user_avg")}: <strong style={{ color: "#a29bfe" }}>{selectedWorker.avg_score ?? "—"}</strong>
                          </span>
                          <span style={{ color: "#a1a1b5", fontSize: "0.85rem" }}>
                            {t("therapist_user_journals")}: <strong style={{ color: "#00cec9" }}>{selectedWorker.journals_count}</strong>
                          </span>
                        </div>
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
