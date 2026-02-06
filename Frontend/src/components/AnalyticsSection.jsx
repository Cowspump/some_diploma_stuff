import React from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import '../styles/App.css';

const AnalyticsSection = () => {
  const wellBeingData = [
    { week: 'Week 1', score: 65 },
    { week: 'Week 2', score: 70 },
    { week: 'Week 3', score: 68 },
    { week: 'Week 4', score: 75 },
    { week: 'Week 5', score: 78 },
    { week: 'Week 6', score: 82 },
  ];

  const satisfactionData = [
    { day: 'Mon', satisfaction: 7 },
    { day: 'Tue', satisfaction: 6 },
    { day: 'Wed', satisfaction: 8 },
    { day: 'Thu', satisfaction: 7 },
    { day: 'Fri', satisfaction: 9 },
    { day: 'Sat', satisfaction: 8 },
    { day: 'Sun', satisfaction: 8 },
  ];

  return (
    <section id="analytics" className="analytics-section py-5">
      <Container>
        <h2 className="section-title text-center mb-5">Your Analytics</h2>

        <Row className="g-4">
          <Col lg={6} className="fade-in-animation">
            <div className="analytics-card p-4">
              <h5 className="mb-4">Well-Being Test Results (Last 6 Weeks)</h5>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={wellBeingData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="week" stroke="#999" />
                  <YAxis stroke="#999" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #ddd',
                      borderRadius: '8px',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#6366f1"
                    strokeWidth={3}
                    dot={{ fill: '#6366f1', r: 5 }}
                    activeDot={{ r: 7 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Col>

          <Col lg={6} className="fade-in-animation">
            <div className="analytics-card p-4">
              <h5 className="mb-4">Life Satisfaction by Day</h5>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={satisfactionData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="day" stroke="#999" />
                  <YAxis stroke="#999" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #ddd',
                      borderRadius: '8px',
                    }}
                  />
                  <Bar
                    dataKey="satisfaction"
                    fill="#8b5cf6"
                    radius={[8, 8, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Col>
        </Row>
      </Container>
    </section>
  );
};

export default AnalyticsSection;