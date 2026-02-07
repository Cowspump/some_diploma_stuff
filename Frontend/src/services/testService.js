import { apiService } from './api';

// Получение списка вопросов с backend
export const fetchTestQuestions = async () => {
  try {
    const response = await apiService.get('/test/questions');
    return response.questions || [];
  } catch (error) {
    console.error('Error fetching test questions:', error);
    throw error;
  }
};

// Сохранение результата теста
export const saveTestResult = async (answers) => {
  try {
    const response = await apiService.post('/test/submit', { answers });
    return response;
  } catch (error) {
    console.error('Error saving test result:', error);
    throw error;
  }
};

// Получение истории результатов
export const getTestResults = async () => {
  try {
    const response = await apiService.get('/test/results');
    return response.results || [];
  } catch (error) {
    console.error('Error fetching test results:', error);
    throw error;
  }
};

// Добавление вопроса (только для терапевтов)
export const addQuestion = async (questionData) => {
  try {
    const response = await apiService.post('/test/add-question', questionData);
    return response;
  } catch (error) {
    console.error('Error adding question:', error);
    throw error;
  }
};

// Удаление вопроса (только для терапевтов)
export const deleteQuestion = async (questionId) => {
  try {
    const response = await apiService.delete(`/test/question/${questionId}`);
    return response;
  } catch (error) {
    console.error('Error deleting question:', error);
    throw error;
  }
};
