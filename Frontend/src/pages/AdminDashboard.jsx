import React, { useEffect, useMemo, useState } from "react";
import { Container, Row, Col, Card, Button, Nav, Navbar, Table, Alert, Spinner, Badge, Dropdown } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/LanguageContext";
import { apiService } from "../services/api";
import "../styles/Dashboard.css";

const AdminDashboard = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const { t, lang, switchLang } = useLanguage();
  const [activeTab, setActiveTab] = useState("stats"); // stats | users | therapists

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [therapists, setTherapists] = useState([]);

  const handleLogout = () => {
    onLogout();
    navigate("/");
  };

  const loadStats = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await apiService.get("/admin/stats");
      setStats(res.counts || null);
    } catch (e) {
      setError(e?.message || t("admin_load_error"));
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await apiService.get("/admin/users?role=worker");
      setUsers(res.users || []);
    } catch (e) {
      setError(e?.message || t("admin_load_error"));
    } finally {
      setLoading(false);
    }
  };

  const loadTherapists = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await apiService.get("/admin/users?role=therapist");
      setTherapists(res.users || []);
    } catch (e) {
      setError(e?.message || t("admin_load_error"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "stats") loadStats();
    if (activeTab === "users") loadUsers();
    if (activeTab === "therapists") loadTherapists();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const handleDeleteWorker = async (u) => {
    if (!u?.id) return;
    if (!window.confirm(`${t("admin_confirm_delete_user")} "${u.full_name}"?`)) return;
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      await apiService.delete(`/admin/user/${u.id}`);
      setSuccess(t("admin_user_deleted"));
      await loadUsers();
      await loadStats();
    } catch (e) {
      setError(e?.message || t("admin_delete_error"));
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTherapist = async (u) => {
    if (!u?.id) return;
    if (!window.confirm(`${t("admin_confirm_delete_therapist")} "${u.full_name}" ${t("admin_confirm_delete_therapist_warn")}`)) return;
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      await apiService.delete(`/admin/therapist/${u.id}`);
      setSuccess(t("admin_therapist_deleted"));
      await loadTherapists();
      await loadStats();
    } catch (e) {
      setError(e?.message || t("admin_delete_error"));
    } finally {
      setLoading(false);
    }
  };

  const statCards = useMemo(() => {
    if (!stats) return [];
    return [
      { title: t("admin_stats_users"), value: stats.users_total, hint: `${t("admin_workers")}: ${stats.users_workers}, ${t("admin_therapists_label")}: ${stats.users_therapists}, ${t("admin_admins")}: ${stats.users_admins}` },
      { title: t("admin_stats_tests"), value: stats.tests_total, hint: `${t("admin_questions")}: ${stats.questions_total}` },
      { title: t("admin_stats_results"), value: stats.test_results_total, hint: `${t("admin_journals")}: ${stats.journals_total}` },
    ];
  }, [stats, t]);

  return (
    <div className="dashboard">
      <Navbar className="navbar-custom shadow-sm" sticky="top">
        <Container>
          <Navbar.Brand className="fw-bold fs-5">{t("admin_title")}</Navbar.Brand>
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
              <span className="me-3">{t("admin_welcome")} {user?.fullName || user?.email}!</span>
              <Button variant="outline-danger" size="sm" onClick={handleLogout}>
                {t("nav_logout")}
              </Button>
            </div>
          </Nav>
        </Container>
      </Navbar>

      <Container className="content-area">
        {error && <Alert variant="danger" dismissible onClose={() => setError("")}>{error}</Alert>}
        {success && <Alert variant="success" dismissible onClose={() => setSuccess("")}>{success}</Alert>}

        <div className="dashboard-tabs">
          <button className={`dashboard-tab ${activeTab === "stats" ? "active" : ""}`} onClick={() => setActiveTab("stats")}>
            {t("admin_tab_stats")}
          </button>
          <button className={`dashboard-tab ${activeTab === "users" ? "active" : ""}`} onClick={() => setActiveTab("users")}>
            {t("admin_tab_users")}
          </button>
          <button className={`dashboard-tab ${activeTab === "therapists" ? "active" : ""}`} onClick={() => setActiveTab("therapists")}>
            {t("admin_tab_therapists")}
          </button>
        </div>

        {loading && (
          <div className="d-flex justify-content-center my-3">
            <Spinner animation="border" role="status" size="sm" />
          </div>
        )}

        {activeTab === "stats" && (
          <>
            <Row className="g-4 mt-1">
              {statCards.map((c) => (
                <Col key={c.title} md={6} lg={3}>
                  <Card className="dashboard-card h-100">
                    <Card.Body>
                      <div className="d-flex justify-content-between align-items-start">
                        <div>
                          <div style={{ color: "#a1a1b5", fontSize: "0.9rem" }}>{c.title}</div>
                          <div style={{ fontSize: "1.8rem", fontWeight: 800 }}>{c.value}</div>
                        </div>
                        <Badge bg="secondary">LIVE</Badge>
                      </div>
                      {c.hint && <div style={{ color: "#6b6b80", fontSize: "0.8rem" }}>{c.hint}</div>}
                    </Card.Body>
                  </Card>
                </Col>
              ))}
            </Row>

            <div className="mt-4">
              <Button variant="outline-secondary" size="sm" onClick={loadStats} disabled={loading}>
                {t("admin_refresh")}
              </Button>
            </div>
          </>
        )}

        {activeTab === "users" && (
          <Card className="dashboard-card mt-3">
            <Card.Body>
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h5 className="mb-0">{t("admin_workers_title")}</h5>
                <Button variant="outline-secondary" size="sm" onClick={loadUsers} disabled={loading}>
                  {t("admin_refresh")}
                </Button>
              </div>
              <Table responsive hover size="sm" className="mb-0">
                <thead>
                  <tr>
                    <th>{t("admin_col_id")}</th>
                    <th>{t("admin_col_name")}</th>
                    <th>{t("admin_col_email")}</th>
                    <th>{t("admin_col_journals")}</th>
                    <th>{t("admin_col_results")}</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id}>
                      <td>{u.id}</td>
                      <td>{u.full_name}</td>
                      <td>{u.mail}</td>
                      <td>{u.journals_count}</td>
                      <td>{u.test_results_count}</td>
                      <td className="text-end">
                        <Button variant="outline-danger" size="sm" onClick={() => handleDeleteWorker(u)} disabled={loading}>
                          {t("admin_delete")}
                        </Button>
                      </td>
                    </tr>
                  ))}
                  {users.length === 0 && (
                    <tr>
                      <td colSpan={6} className="text-center text-muted py-4">
                        {t("admin_no_users")}
                      </td>
                    </tr>
                  )}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        )}

        {activeTab === "therapists" && (
          <Card className="dashboard-card mt-3">
            <Card.Body>
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h5 className="mb-0">{t("admin_therapists_title")}</h5>
                <Button variant="outline-secondary" size="sm" onClick={loadTherapists} disabled={loading}>
                  {t("admin_refresh")}
                </Button>
              </div>
              <Table responsive hover size="sm" className="mb-0">
                <thead>
                  <tr>
                    <th>{t("admin_col_id")}</th>
                    <th>{t("admin_col_name")}</th>
                    <th>{t("admin_col_email")}</th>
                    <th>{t("admin_col_tests")}</th>
                    <th>{t("admin_col_materials")}</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {therapists.map((u) => (
                    <tr key={u.id}>
                      <td>{u.id}</td>
                      <td>{u.full_name}</td>
                      <td>{u.mail}</td>
                      <td>{u.tests_created_count}</td>
                      <td>{u.materials_count}</td>
                      <td className="text-end">
                        <Button variant="outline-danger" size="sm" onClick={() => handleDeleteTherapist(u)} disabled={loading}>
                          {t("admin_delete")}
                        </Button>
                      </td>
                    </tr>
                  ))}
                  {therapists.length === 0 && (
                    <tr>
                      <td colSpan={6} className="text-center text-muted py-4">
                        {t("admin_no_therapists")}
                      </td>
                    </tr>
                  )}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        )}

      </Container>
    </div>
  );
};

export default AdminDashboard;
