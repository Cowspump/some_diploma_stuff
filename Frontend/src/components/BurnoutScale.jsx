import React, { useState, useEffect } from "react";
import { Container, Row, Col, Spinner } from "react-bootstrap";
import { useLanguage } from "../contexts/LanguageContext";
import { apiService } from "../services/api";
import "../styles/App.css";

const BurnoutScale = () => {
  const { t } = useLanguage();
  const [burnoutLevel, setBurnoutLevel] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) loadData();
    else setLoading(false);
  }, []);

  const loadData = async () => {
    try {
      const [testRes, journalRes] = await Promise.all([
        apiService.get("/test/results").catch(() => ({ results: [] })),
        apiService.get("/journal").catch(() => ({ journals: [] })),
      ]);
      const results = testRes.results || [];
      const journals = journalRes.journals || [];
      if (results.length === 0 && journals.length === 0) { setBurnoutLevel(null); return; }

      let riskScore = 50;
      if (results.length > 0) {
        const avgTest = results.reduce((s, r) => s + r.total_score, 0) / results.length;
        riskScore = Math.max(0, 100 - avgTest);
      }
      if (journals.length > 0) {
        const avgMood = journals.reduce((s, j) => s + j.wellbeing_score, 0) / journals.length;
        const moodRisk = ((5 - avgMood) / 5) * 100;
        riskScore = Math.round((riskScore + moodRisk) / 2);
      }
      setBurnoutLevel(Math.min(100, Math.max(0, riskScore)));
    } catch (err) {
      console.error("BurnoutScale error:", err);
    } finally {
      setLoading(false);
    }
  };

  const getLabel = (level) => {
    if (level >= 70) return t("burnout_high");
    if (level >= 40) return t("burnout_medium");
    return t("burnout_low");
  };

  const getColor = (level) => {
    if (level >= 70) return "#dc3545";
    if (level >= 40) return "#ffc107";
    return "#28a745";
  };

  return (
    <section id="burnout" className="burnout-section py-5">
      <Container>
        <h2 className="section-title text-center mb-5">{t("burnout_title")}</h2>
        <Row>
          <Col lg={8} className="mx-auto">
            <div className="burnout-card p-5 fade-in-animation">
              {loading ? (
                <div className="text-center"><Spinner animation="border" /></div>
              ) : burnoutLevel === null ? (
                <p className="text-center text-muted">{t("burnout_no_data")}</p>
              ) : (
                <>
                  <div className="d-flex justify-content-between align-items-center mb-3">
                    <span className="burnout-label">{t("burnout_label")}</span>
                    <span className="burnout-percentage fw-bold" style={{ color: getColor(burnoutLevel) }}>{burnoutLevel}%</span>
                  </div>
                  <div className="burnout-progress-bar">
                    <div className="burnout-progress-fill" style={{ width: `${burnoutLevel}%`, backgroundColor: getColor(burnoutLevel) }}></div>
                  </div>
                  <p className="mt-4 mb-0 text-muted"><small>{getLabel(burnoutLevel)}</small></p>
                </>
              )}
            </div>
          </Col>
        </Row>
      </Container>
    </section>
  );
};

export default BurnoutScale;
