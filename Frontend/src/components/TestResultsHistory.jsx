import React, { useState, useEffect } from "react";
import { Container, Row, Col, Card, Button, Badge, Modal, Alert } from "react-bootstrap";
import { useLanguage } from "../contexts/LanguageContext";
import { getTestResults } from "../services/testService";
import { getLocale } from "../i18n/locale";
import "../styles/TestResultsHistory.css";

const TestResultsHistory = ({ userId }) => {
  const { t, lang } = useLanguage();
  const [results, setResults] = useState([]);
  const [selectedResult, setSelectedResult] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) loadResults();
  }, [userId, lang]);

  const loadResults = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getTestResults(lang);
      setResults((data || []).sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));
    } catch (err) {
      if (!err.message?.includes("Only workers")) setError(t("results_load_error"));
    } finally {
      setLoading(false);
    }
  };

  const getScoreBadge = (score) => {
    if (score >= 80) return <Badge bg="success">{t("results_excellent")}</Badge>;
    if (score >= 60) return <Badge bg="info">{t("results_good")}</Badge>;
    if (score >= 40) return <Badge bg="warning">{t("results_average")}</Badge>;
    return <Badge bg="danger">{t("results_attention")}</Badge>;
  };

  const formatDate = (ds) =>
    new Date(ds).toLocaleDateString(getLocale(lang), {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });

  return (
    <section id="results" className="results-history-section py-5">
      <Container>
        <div className="section-header mb-5">
          <h2 className="section-title">{t("results_title")}</h2>
          <p className="section-description">{t("results_desc")}</p>
        </div>
        {error && <Alert variant="danger" className="mb-4">{error}</Alert>}
        {loading && <Row><Col className="text-center py-5"><div className="spinner-border" role="status"><span className="visually-hidden">...</span></div></Col></Row>}
        {!loading && results.length === 0 && !error ? (
          <Row><Col lg={8} className="mx-auto"><Card className="empty-state text-center py-5"><Card.Body><h5 className="mb-3">{t("results_none")}</h5><p className="text-muted">{t("results_none_desc")}</p></Card.Body></Card></Col></Row>
        ) : (
          <>
            <Row className="mb-4"><Col><div className="d-flex justify-content-between align-items-center"><p className="text-muted mb-0">{t("results_total")} <strong>{results.length}</strong></p><Button variant="outline-primary" size="sm" onClick={loadResults}>{t("results_refresh")}</Button></div></Col></Row>
            <Row className="g-4">
              {results.map((result, index) => (
                <Col lg={6} key={result.id}>
                  <Card className="result-card h-100 shadow-sm">
                    <Card.Body>
                      <div className="d-flex justify-content-between align-items-start mb-3">
                        <div><h5 className="mb-1">{result.test_title || `#${results.length - index}`}</h5><p className="text-muted small mb-0">{formatDate(result.created_at)}</p></div>
                        {getScoreBadge(result.total_score)}
                      </div>
                      <div className="score-display mb-3"><div className="score-circle"><span className="score-value">{result.total_score}</span></div></div>
                      <div className="progress mb-3"><div className="progress-bar" role="progressbar" style={{ width: `${Math.min(100, (result.total_score / 100) * 100)}%` }}></div></div>
                      <Button variant="outline-primary" size="sm" className="w-100" onClick={() => { setSelectedResult(result); setShowDetailsModal(true); }}>{t("results_details")}</Button>
                    </Card.Body>
                  </Card>
                </Col>
              ))}
            </Row>
          </>
        )}
      </Container>
      <Modal show={showDetailsModal} onHide={() => setShowDetailsModal(false)} centered>
        <Modal.Header closeButton><Modal.Title>{t("results_modal_title")}</Modal.Title></Modal.Header>
        <Modal.Body>
          {selectedResult && (
            <div className="text-center">
              <div className="score-circle-large mx-auto mb-3"><span className="score-value-large">{selectedResult.total_score}</span></div>
              <h6>{selectedResult.test_title || ""}</h6>
              <p className="text-muted">{formatDate(selectedResult.created_at)}</p>
              {getScoreBadge(selectedResult.total_score)}
            </div>
          )}
        </Modal.Body>
        <Modal.Footer><Button variant="secondary" onClick={() => setShowDetailsModal(false)}>{t("test_close")}</Button></Modal.Footer>
      </Modal>
    </section>
  );
};

export default TestResultsHistory;
