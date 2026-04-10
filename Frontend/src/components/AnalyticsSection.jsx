import React, { useState, useEffect } from "react";
import { Container, Row, Col, Spinner } from "react-bootstrap";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { useLanguage } from "../contexts/LanguageContext";
import { apiService } from "../services/api";
import { getLocale } from "../i18n/locale";
import "../styles/App.css";

const AnalyticsSection = () => {
  const { t, lang } = useLanguage();
  const [testData, setTestData] = useState([]);
  const [moodData, setMoodData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) loadData();
    else setLoading(false);
  }, [lang]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [testRes, journalRes] = await Promise.all([
        apiService.get("/test/results").catch(() => ({ results: [] })),
        apiService.get(`/journal?lang=${encodeURIComponent(lang || "ru")}`).catch(() => ({ journals: [] })),
      ]);
      setTestData(
        (testRes.results || [])
          .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
          .map((r) => ({
            name: new Date(r.created_at).toLocaleDateString(getLocale(lang), { day: "2-digit", month: "short" }),
            score: r.total_score,
          }))
      );
      setMoodData(
        (journalRes.journals || [])
          .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
          .map((j) => ({
            day: new Date(j.created_at).toLocaleDateString(getLocale(lang), { weekday: "short" }),
            mood: j.wellbeing_score,
          }))
      );
    } catch (err) {
      console.error("Analytics load error:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <section id="analytics" className="analytics-section py-5"><Container className="text-center"><Spinner animation="border" /></Container></section>;
  }

  const noData = testData.length === 0 && moodData.length === 0;

  return (
    <section id="analytics" className="analytics-section py-5">
      <Container>
        <h2 className="section-title text-center mb-5">{t("analytics_title")}</h2>
        {noData ? (
          <p className="text-center text-muted">{t("analytics_no_data")}</p>
        ) : (
          <Row className="g-4">
            <Col lg={6} className="fade-in-animation">
              <div className="analytics-card p-4">
                <h5 className="mb-4">{t("analytics_tests")}</h5>
                {testData.length === 0 ? <p className="text-muted">{t("analytics_no_tests")}</p> : (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={testData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="name" stroke="#999" />
                      <YAxis stroke="#999" />
                      <Tooltip contentStyle={{ backgroundColor: "#fff", border: "1px solid #ddd", borderRadius: "8px" }} />
                      <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={3} dot={{ fill: "#6366f1", r: 5 }} activeDot={{ r: 7 }} />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>
            </Col>
            <Col lg={6} className="fade-in-animation">
              <div className="analytics-card p-4">
                <h5 className="mb-4">{t("analytics_mood")}</h5>
                {moodData.length === 0 ? <p className="text-muted">{t("analytics_no_mood")}</p> : (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={moodData}>
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
        )}
      </Container>
    </section>
  );
};

export default AnalyticsSection;
