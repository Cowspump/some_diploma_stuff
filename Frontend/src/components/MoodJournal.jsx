import React, { useState } from 'react';
import { Container, Row, Col, Form, Button, Alert } from 'react-bootstrap';
import '../styles/App.css';

const MoodJournal = ({ isLoggedIn }) => {
  const [moodEntry, setMoodEntry] = useState('');
  const [currentMood, setCurrentMood] = useState('neutral');
  const [submitted, setSubmitted] = useState(false);

  const moodOptions = [
    { value: 'very-bad', label: '😢', name: 'Very Bad' },
    { value: 'bad', label: '😟', name: 'Bad' },
    { value: 'neutral', label: '😐', name: 'Neutral' },
    { value: 'good', label: '🙂', name: 'Good' },
    { value: 'very-good', label: '😄', name: 'Very Good' },
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (moodEntry.trim()) {
      setSubmitted(true);
      setMoodEntry('');
      setTimeout(() => setSubmitted(false), 3000);
    }
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
                  Please log in to write mood entries and track your emotional journey.
                </p>
              </Alert>
            ) : (
              <div className="journal-form fade-in-animation">
                <Form onSubmit={handleSubmit}>
                  <Form.Group className="mb-4">
                    <Form.Label className="mb-3 fs-6 fw-500">How are you feeling today?</Form.Label>
                    <div className="mood-selector d-flex justify-content-center gap-3">
                      {moodOptions.map((mood) => (
                        <button
                          key={mood.value}
                          type="button"
                          className={`mood-btn ${currentMood === mood.value ? 'active' : ''}`}
                          onClick={() => setCurrentMood(mood.value)}
                          title={mood.name}
                        >
                          {mood.label}
                        </button>
                      ))}
                    </div>
                  </Form.Group>

                  <Form.Group className="mb-4">
                    <Form.Label htmlFor="moodText" className="mb-2">Share your thoughts</Form.Label>
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
            )}
          </Col>
        </Row>
      </Container>
    </section>
  );
};

export default MoodJournal;