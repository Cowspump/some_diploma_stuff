import { apiService } from './api';

class AuthService {
  async login(email, password) {
    const response = await apiService.post('/auth/login', {
      email,
      password,
    });
    return response;
  }

  async register(userData) {
    const response = await apiService.post('/auth/register', {
      full_name: userData.fullName,
      email: userData.email,
      birth_date: userData.birthDate,
      role: userData.role,
      password: userData.password,
    });
    return response;
  }

  async getCurrentUser() {
    return await apiService.get('/auth/me');
  }

  async refreshToken() {
    return await apiService.post('/auth/refresh');
  }
}

export const authService = new AuthService();
