/**
 * Zustand store for authentication state management
 * Handles login, logout, and user profile data
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import Cookies from 'js-cookie';
import type { UserProfile, RegisterRequest } from '@/types/api';
import { apiClient } from '@/lib/api-client';

/**
 * Auth state interface
 */
interface AuthState {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  accessToken: string | null;
  refreshToken: string | null;
}

/**
 * Auth actions interface
 */
interface AuthActions {
  /**
   * Register new user
   * @param data - Registration data
   */
  register: (data: RegisterRequest) => Promise<{ accessCode: string }>;

  /**
   * Login with access code
   * @param accessCode - User access code (XXX-XXX-XXX)
   */
  login: (accessCode: string) => Promise<void>;

  /**
   * Logout user and clear tokens
   */
  logout: () => void;

  /**
   * Refresh user profile data
   */
  refreshUser: () => Promise<void>;

  /**
   * Set user profile
   * @param user - User profile data
   */
  setUser: (user: UserProfile | null) => void;

  /**
   * Set tokens in state and cookies
   * @param accessToken - JWT access token
   * @param refreshToken - JWT refresh token
   */
  setTokens: (accessToken: string, refreshToken: string) => void;

  /**
   * Clear error message
   */
  clearError: () => void;

  /**
   * Initialize store from cookies
   */
  initialize: () => void;
}

/**
 * Auth store with persistence
 * Saves user and isAuthenticated to localStorage
 */
export const useAuthStore = create<AuthState & AuthActions>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      accessToken: null,
      refreshToken: null,

      // Actions
      register: async (data: RegisterRequest) => {
        set({ isLoading: true, error: null });

        try {
          // Call backend register endpoint
          const response = await apiClient.register(data);

          // Store tokens in cookies and state
          get().setTokens(response.access_token, response.refresh_token);

          // Fetch user profile after registration
          const profile = await apiClient.getProfile();

          // Set user data
          set({
            user: profile,
            isAuthenticated: true,
            isLoading: false,
            error: null
          });

          // Return access code to show to user
          return { accessCode: response.access_code };
        } catch (error: any) {
          console.error('Register error:', error);
          set({
            error: error.message || 'Registration failed',
            isLoading: false,
            isAuthenticated: false,
            user: null
          });
          throw error;
        }
      },

      login: async (accessCode: string) => {
        set({ isLoading: true, error: null });

        try {
          // Call backend login endpoint directly via Next.js rewrite
          const response = await apiClient.login(accessCode);

          // Store tokens in cookies and state
          get().setTokens(response.access_token, response.refresh_token);

          // Set user data from login response (no need for separate getProfile call)
          set({
            user: response.user,
            isAuthenticated: true,
            isLoading: false,
            error: null
          });
        } catch (error: any) {
          console.error('Login error:', error);
          set({
            error: error.message || 'Login failed',
            isLoading: false,
            isAuthenticated: false,
            user: null
          });
          throw error;
        }
      },

      logout: async () => {
        // Clear cookies
        Cookies.remove('access_token');
        Cookies.remove('refresh_token');

        // Clear state
        set({
          user: null,
          isAuthenticated: false,
          error: null,
          accessToken: null,
          refreshToken: null
        });

        // Redirect to login
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
      },

      refreshUser: async () => {
        const { isAuthenticated } = get();

        if (!isAuthenticated) {
          return;
        }

        try {
          const profile = await apiClient.getProfile();
          set({ user: profile });
        } catch (error: any) {
          console.error('Refresh user error:', error);

          // If 401, logout
          if (error.response?.status === 401) {
            get().logout();
          }
        }
      },

      setUser: (user: UserProfile | null) => {
        set({ user });
      },

      setTokens: (accessToken: string, refreshToken: string) => {
        // Store in cookies (30 minutes for access, 7 days for refresh)
        Cookies.set('access_token', accessToken, { expires: 1/48 }); // 30 minutes = 1/48 day
        Cookies.set('refresh_token', refreshToken, { expires: 7 });

        // Store in state for immediate access
        set({
          accessToken,
          refreshToken,
          isAuthenticated: true
        });
      },

      initialize: () => {
        // Read tokens from cookies on app initialization
        const accessToken = Cookies.get('access_token');
        const refreshToken = Cookies.get('refresh_token');

        if (accessToken && refreshToken) {
          set({
            accessToken,
            refreshToken,
            isAuthenticated: true
          });
        }
      },

      clearError: () => {
        set({ error: null });
      }
    }),
    {
      name: 'auth-storage',
      // Persist user, tokens and isAuthenticated
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken
      })
    }
  )
);

