import { apiService } from "./api";

export const getAIChatHistory = async (limit = 50) => {
  const response = await apiService.get(`/ai/chat-history?limit=${limit}`);
  return response.history || [];
};

