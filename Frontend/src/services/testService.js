// Симуляция API для вопросов теста (потом заменить на реальную БД)
export const fetchTestQuestions = async () => {
  // Временные данные - замените на реальный API запрос
  return [
    {
      id: 1,
      question: "Как вы себя чувствуете?",
      options: ["Отлично", "Хорошо", "Нормально", "Плохо"],
    },
    {
      id: 2,
      question: "Уровень стресса?",
      options: ["Низкий", "Средний", "Высокий", "Очень высокий"],
    },
    {
      id: 3,
      question: "Качество сна?",
      options: ["Отличное", "Хорошее", "Удовлетворительное", "Плохое"],
    },
  ];
};

// Сохранение результата теста
export const saveTestResult = async (userId, answers, score) => {
  const result = {
    id: Date.now(),
    userId,
    timestamp: new Date().toISOString(),
    answers,
    score,
  };

  // Сохранение в localStorage (потом заменить на API запрос)
  const results = JSON.parse(localStorage.getItem("testResults") || "[]");
  results.push(result);
  localStorage.setItem("testResults", JSON.stringify(results));

  return result;
};

// Получение истории результатов
export const getTestResults = (userId) => {
  const allResults = JSON.parse(localStorage.getItem("testResults") || "[]");
  return allResults.filter((r) => r.userId === userId);
};
