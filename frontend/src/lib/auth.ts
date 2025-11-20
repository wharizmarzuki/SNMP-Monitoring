/**
 * Authentication service for managing user authentication
 */
import { api } from "./api";

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserInfo {
  id: number;
  username: string;
  email: string;
  is_admin: boolean;
  is_active: boolean;
}

export interface ChangePasswordData {
  current_password: string;
  new_password: string;
}

export interface ChangeEmailData {
  new_email: string;
  password: string;
}

const TOKEN_KEY = "snmp_auth_token";
const USER_KEY = "snmp_user_info";

/**
 * Authentication service
 */
export const authService = {
  /**
   * Login with username and password
   */
  login: async (credentials: LoginCredentials): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>("/auth/login", credentials);
    const { access_token, token_type } = response.data;

    // Store token
    if (typeof window !== "undefined") {
      localStorage.setItem(TOKEN_KEY, access_token);
    }

    return response.data;
  },

  /**
   * Logout - clear token and user info
   */
  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    }
  },

  /**
   * Get stored token
   */
  getToken: (): string | null => {
    if (typeof window !== "undefined") {
      return localStorage.getItem(TOKEN_KEY);
    }
    return null;
  },

  /**
   * Check if user is authenticated (has token)
   */
  isAuthenticated: (): boolean => {
    return !!authService.getToken();
  },

  /**
   * Get current user information from API
   */
  getCurrentUser: async (): Promise<UserInfo> => {
    const response = await api.get<UserInfo>("/auth/me");

    // Cache user info
    if (typeof window !== "undefined") {
      localStorage.setItem(USER_KEY, JSON.stringify(response.data));
    }

    return response.data;
  },

  /**
   * Get cached user info (from localStorage)
   */
  getCachedUser: (): UserInfo | null => {
    if (typeof window !== "undefined") {
      const cached = localStorage.getItem(USER_KEY);
      if (cached) {
        try {
          return JSON.parse(cached);
        } catch {
          return null;
        }
      }
    }
    return null;
  },

  /**
   * Change password
   */
  changePassword: async (data: ChangePasswordData): Promise<void> => {
    await api.put("/auth/me/password", data);
  },

  /**
   * Change email
   */
  changeEmail: async (data: ChangeEmailData): Promise<void> => {
    const response = await api.put("/auth/me/email", data);

    // Update cached user info with new email
    const cachedUser = authService.getCachedUser();
    if (cachedUser && typeof window !== "undefined") {
      cachedUser.email = data.new_email;
      localStorage.setItem(USER_KEY, JSON.stringify(cachedUser));
    }

    return response.data;
  },
};

/**
 * Setup axios interceptor to inject auth token
 */
export function setupAuthInterceptor() {
  // Request interceptor - add token to headers
  api.interceptors.request.use(
    (config) => {
      const token = authService.getToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor - handle 401 errors
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      // Check both error formats (AxiosError and transformed error from api.ts)
      if (error.response?.status === 401 || error.status === 401) {
        // Unauthorized - clear auth and redirect to login
        authService.logout();

        // Only redirect on client side
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
      }
      return Promise.reject(error);
    }
  );
}
