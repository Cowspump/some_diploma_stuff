import React, { useEffect, useMemo, useState } from "react";
import { Container, Row, Col, Card, Button, Modal, Form } from "react-bootstrap";
import { motion } from "framer-motion";
import { useLanguage } from "../contexts/LanguageContext";
import { useAuth } from "../contexts/AuthContext";
import { apiService } from "../services/api";
import "../styles/App.css";

const MaterialsSection = () => {
  const { t } = useLanguage();
  const { user } = useAuth();
  const [materials, setMaterials] = useState([]);
  const [selected, setSelected] = useState(null);
  const [showView, setShowView] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [newMat, setNewMat] = useState({ title: "", content: "" });
  const [saving, setSaving] = useState(false);

  const builtInMaterials = useMemo(() => ([
    { id: "builtin-1", title: t("mat_burnout_title"), description: t("mat_burnout_desc"), icon: "🔥", content: t("mat_burnout_desc") },
    { id: "builtin-2", title: t("mat_mindfulness_title"), description: t("mat_mindfulness_desc"), icon: "🧘", content: t("mat_mindfulness_desc") },
    { id: "builtin-3", title: t("mat_sleep_title"), description: t("mat_sleep_desc"), icon: "😴", content: t("mat_sleep_desc") },
    { id: "builtin-4", title: t("mat_stress_title"), description: t("mat_stress_desc"), icon: "🌿", content: t("mat_stress_desc") },
  ]), [t]);

  useEffect(() => {
    (async () => {
      try {
        const res = await apiService.get("/materials");
        setMaterials(res.materials || []);
      } catch {
        setMaterials([]);
      }
    })();
  }, []);

  const allMaterials = useMemo(() => {
    const apiMats = (materials || []).map((m) => ({
      id: `api-${m.id}`,
      title: m.title,
      description: (m.content || "").slice(0, 90) + ((m.content || "").length > 90 ? "..." : ""),
      icon: "📘",
      content: m.content,
    }));
    return [...builtInMaterials, ...apiMats];
  }, [builtInMaterials, materials]);

  const canAdd = user?.role === "therapist" || user?.role === "admin";

  const handleOpen = (m) => {
    setSelected(m);
    setShowView(true);
  };

  const handleCreate = async () => {
    if (!newMat.title.trim() || !newMat.content.trim()) return;
    setSaving(true);
    try {
      await apiService.post("/materials", newMat);
      const res = await apiService.get("/materials");
      setMaterials(res.materials || []);
      setShowAdd(false);
      setNewMat({ title: "", content: "" });
    } finally {
      setSaving(false);
    }
  };

  return (
    <section id="materials" className="materials-section py-5">
      <Container>
        <motion.h2
          className="section-title text-center mb-5"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
        >
          {t("materials_title")}
        </motion.h2>
        <div className="d-flex justify-content-between align-items-center mb-3">
          <div />
          {canAdd && (
            <Button variant="outline-primary" size="sm" onClick={() => setShowAdd(true)}>
              {t("materials_add")}
            </Button>
          )}
        </div>

        <Row className="g-4">
          {allMaterials.map((m, index) => (
            <Col key={m.id} md={6} lg={3}>
              <motion.div
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                whileHover={{ y: -8 }}
              >
                <Card className="material-card h-100 border-0 shadow-sm" style={{ cursor: "pointer" }} onClick={() => handleOpen(m)}>
                  <Card.Body className="d-flex flex-column">
                    <motion.div
                      className="material-icon mb-3"
                      whileHover={{ scale: 1.2, rotate: 10 }}
                      transition={{ type: "spring", stiffness: 300 }}
                    >
                      {m.icon}
                    </motion.div>
                    <Card.Title className="material-title">{m.title}</Card.Title>
                    <Card.Text className="material-text flex-grow-1">{m.description}</Card.Text>
                    <span className="material-link mt-2">{t("materials_learn_more")}</span>
                  </Card.Body>
                </Card>
              </motion.div>
            </Col>
          ))}
        </Row>

        {/* Oil & Gas Banner */}
        <motion.div
          className="oil-gas-banner mt-5"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ duration: 0.6 }}
        >
          <img src="/images/hero-mental-health.jpg" alt="Mental Health Resources" />
          <div className="oil-gas-overlay">
            <h3>{t("mat_stress_title")}</h3>
            <p>{t("mat_stress_desc")}</p>
          </div>
        </motion.div>
      </Container>

      <Modal show={showView} onHide={() => setShowView(false)} centered size="lg">
        <Modal.Header closeButton>
          <Modal.Title>{selected?.title || t("materials_title")}</Modal.Title>
        </Modal.Header>
        <Modal.Body style={{ whiteSpace: "pre-wrap" }}>
          {selected?.content || ""}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowView(false)}>{t("test_close")}</Button>
        </Modal.Footer>
      </Modal>

      <Modal show={showAdd} onHide={() => setShowAdd(false)} centered size="lg">
        <Modal.Header closeButton>
          <Modal.Title>{t("materials_add_title")}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>{t("materials_field_title")}</Form.Label>
              <Form.Control value={newMat.title} onChange={(e) => setNewMat((p) => ({ ...p, title: e.target.value }))} />
            </Form.Group>
            <Form.Group>
              <Form.Label>{t("materials_field_content")}</Form.Label>
              <Form.Control as="textarea" rows={8} value={newMat.content} onChange={(e) => setNewMat((p) => ({ ...p, content: e.target.value }))} />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowAdd(false)}>{t("therapist_cancel")}</Button>
          <Button variant="primary" onClick={handleCreate} disabled={saving || !newMat.title.trim() || !newMat.content.trim()}>
            {saving ? t("therapist_saving") : t("materials_publish")}
          </Button>
        </Modal.Footer>
      </Modal>
    </section>
  );
};

export default MaterialsSection;
