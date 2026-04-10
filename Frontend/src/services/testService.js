import { apiService } from './api';

// --- Тесты (CRUD) ---
export const createTest = async (testData) => {
  const response = await apiService.post('/test/create', testData);
  return response;
};

export const getTests = async (lang = "ru") => {
  // Always request language explicitly so RU can also be served as a translation
  // for tests whose source_lang is not Russian.
  const endpoint = `/tests?lang=${encodeURIComponent(lang || "ru")}`;
  const response = await apiService.get(endpoint);
  return response.tests || [];
};

export const deleteTest = async (testId) => {
  const response = await apiService.delete(`/test/${testId}`);
  return response;
};

// --- Вопросы ---
export const fetchTestQuestions = async (testId, lang = "ru") => {
  // Always request language explicitly so RU can also be served as a translation
  // for questions whose source_lang is not Russian.
  const base = testId ? `/test/questions?test_id=${testId}` : "/test/questions";
  const endpoint = `${base}${base.includes("?") ? "&" : "?"}lang=${encodeURIComponent(lang || "ru")}`;
  const response = await apiService.get(endpoint);
  return response.questions || [];
};

export const saveTestResult = async (answers, testId) => {
  const payload = { answers };
  if (testId) payload.test_id = testId;
  const response = await apiService.post('/test/submit', payload);
  return response;
};

export const getTestResults = async (lang = "ru") => {
  let endpoint = '/test/results';
  if (lang && lang !== "ru") {
    endpoint += `?lang=${lang}`;
  }
  const response = await apiService.get(endpoint);
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
export const explainQuestion = async (questionId, lang = "ru") => {
  const response = await apiService.post('/ai/explain-question', { question_id: questionId, lang });
  return response;
};
