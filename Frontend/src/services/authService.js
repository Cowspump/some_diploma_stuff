import { apiService } from "./api";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

class AuthService {
  async login(email, password) {
    // Backend использует OAuth2PasswordRequestForm
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const response = await fetch(`${API_BASE_URL}/token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Login failed");
    }

    const data = await response.json();
    return {
      access_token: data.access_token,
      token_type: data.token_type,
      user: data.user,
    };
  }

  async register(userData) {
    const response = await fetch(`${API_BASE_URL}/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        full_name: userData.fullName,
        mail: userData.email,
        password: userData.password,
        role: userData.role,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Registration failed");
    }

    return await response.json();
  }

  async getCurrentUser() {
    return await apiService.get("/auth/me");
  }
}

export const authService = new AuthService();
