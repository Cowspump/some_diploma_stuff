import React, { useEffect, useMemo, useState } from "react";
import { Container, Row, Col, Card, Button, Modal } from "react-bootstrap";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import rehypeSanitize from "rehype-sanitize";
import { useLanguage } from "../contexts/LanguageContext";
import { apiService } from "../services/api";
import "../styles/App.css";

const ICONS = ["🔥", "🧘", "😴", "🌿", "📘", "💡", "🧠", "🎯"];

const MaterialsSection = () => {
  const { t, lang } = useLanguage();
  const [materials, setMaterials] = useState([]);
  const [selected, setSelected] = useState(null);
  const [showView, setShowView] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        // Always request language explicitly so RU can also be served as a translation
        // for materials whose source_lang is not Russian.
        const endpoint = `/materials?lang=${encodeURIComponent(lang || "ru")}`;
        const res = await apiService.get(endpoint);
        setMaterials(res.materials || []);
      } catch {
        setMaterials([]);
      }
    })();
  }, [lang]);

  const allMaterials = useMemo(() => {
    return (materials || []).map((m, i) => ({
      id: m.id,
      title: m.title,
      description: (m.content || "").slice(0, 90) + ((m.content || "").length > 90 ? "..." : ""),
      icon: (m.emoji && String(m.emoji).trim()) ? String(m.emoji).trim() : ICONS[i % ICONS.length],
      content: m.content,
    }));
  }, [materials]);

  const handleOpen = (m) => {
    setSelected(m);
    setShowView(true);
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
            <h3>{allMaterials[0]?.title || t("materials_title")}</h3>
            <p>{allMaterials[0]?.description || ""}</p>
          </div>
        </motion.div>
      </Container>

      <Modal show={showView} onHide={() => setShowView(false)} centered size="lg">
        <Modal.Header closeButton>
          <Modal.Title>{selected?.title || t("materials_title")}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="markdown-body" style={{ color: "inherit" }}>
            <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]} rehypePlugins={[rehypeSanitize]}>
              {selected?.content || ""}
            </ReactMarkdown>
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowView(false)}>{t("test_close")}</Button>
        </Modal.Footer>
      </Modal>

    </section>
  );
};

export default MaterialsSection;
