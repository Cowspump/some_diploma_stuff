import { apiService } from './api';

// --- Тесты (CRUD) ---
export const createTest = async (testData) => {
  const response = await apiService.post('/test/create', testData);
  return response;
};

export const getTests = async () => {
  const response = await apiService.get('/tests');
  return response.tests || [];
};

export const deleteTest = async (testId) => {
  const response = await apiService.delete(`/test/${testId}`);
  return response;
};

// --- Вопросы ---
export const fetchTestQuestions = async (testId) => {
  const endpoint = testId ? `/test/questions?test_id=${testId}` : '/test/questions';
  const response = await apiService.get(endpoint);
  return response.questions || [];
};

export const saveTestResult = async (answers, testId) => {
  const payload = { answers };
  if (testId) payload.test_id = testId;
  const response = await apiService.post('/test/submit', payload);
  return response;
};

export const getTestResults = async () => {
  const response = await apiService.get('/test/results');
  return response.results || [];
};

export const addQuestion = async (questionData) => {
  const response = await apiService.post('/test/add-question', questionData);
  return response;
};

export const deleteQuestion = async (questionId) => {
  const response = await apiService.delete(`/test/question/${questionId}`);
  return response;
};

// --- AI объяснение вопроса ---
export const explainQuestion = async (questionId) => {
  const response = await apiService.post('/ai/explain-question', { question_id: questionId });
  return response;
};
