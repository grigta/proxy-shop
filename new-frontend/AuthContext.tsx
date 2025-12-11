import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { AxiosError } from 'axios';
import { apiClient } from './lib/api-client';
import type {
  LoginResponse,
  RegisterResponse,
  UserProfile,
  APIError
} from './types/api';
import { PlatformType } from './types/api';
import {
  ACCESS_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
  USER_DATA_KEY
} from './lib/constants';

/**
 * Helper function to format API error details into a user-friendly string
 * Handles both Pydantic validation errors (array) and simple string errors
 */
const formatAPIError = (detail: unknown): string => {
  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail)) {
    // Pydantic validation errors format: [{ loc: [...], msg: "...", type: "..." }]
    return detail
      .map((err: any) => {
        const field = err.loc ? err.loc.slice(1).join('.') : 'field';
        const message = err.msg || 'validation error';
        return field ? `${field}: ${message}` : message;
      })
      .join(', ');
  }

  // Handle object errors
  if (typeof detail === 'object' && detail !== null) {
    return JSON.stringify(detail);
  }

  return 'An unexpected error occurred';
};

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (code: string) => Promise<void>;
  register: (language?: string) => Promise<string>;
  logout: () => void;
  clearError: () => void;
  updateUser: (user: UserProfile | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const logout = useCallback(() => {
    // Clear all localStorage items
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_DATA_KEY);

    // Reset state
    setUser(null);
    setError(null);
  }, []);

  useEffect(() => {
    // Initialize user from localStorage on mount
    const initializeAuth = async () => {
      const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
      const userData = localStorage.getItem(USER_DATA_KEY);

      if (accessToken && userData) {
        try {
          const parsedUser = JSON.parse(userData) as UserProfile;
          setUser(parsedUser);

          // Optionally verify token validity
          try {
            await apiClient.verifyToken();
          } catch (err) {
            // Token is invalid, logout silently
            console.warn('Token verification failed, logging out');
            logout();
          }
        } catch (err) {
          console.error('Failed to parse user data from localStorage', err);
          logout();
        }
      }
    };

    initializeAuth();
  }, [logout]);

  const login = async (code: string) => {
    setIsLoading(true);
    setError(null);

    try {
      // Normalize access code to uppercase
      const normalizedCode = code.toUpperCase();

      // Call backend login
      const loginResponse: LoginResponse = await apiClient.login(normalizedCode);

      // Store tokens in localStorage
      localStorage.setItem(ACCESS_TOKEN_KEY, loginResponse.access_token);
      localStorage.setItem(REFRESH_TOKEN_KEY, loginResponse.refresh_token);

      // Fetch full user profile
      const userProfile: UserProfile = await apiClient.getProfile();

      // Store user profile in localStorage
      localStorage.setItem(USER_DATA_KEY, JSON.stringify(userProfile));

      // Update user state
      setUser(userProfile);
    } catch (err) {
      const axiosError = err as AxiosError<APIError>;
      const errorMessage = formatAPIError(axiosError.response?.data?.detail) || 'Login failed. Please try again.';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (language?: string): Promise<string> => {
    setIsLoading(true);
    setError(null);

    try {
      // Call backend register with WEB platform
      const registerResponse: RegisterResponse = await apiClient.register({
        platform: PlatformType.WEB,
        language: language || 'en'
      });

      // Store tokens in localStorage
      localStorage.setItem(ACCESS_TOKEN_KEY, registerResponse.access_token);
      localStorage.setItem(REFRESH_TOKEN_KEY, registerResponse.refresh_token);

      // Fetch full user profile
      const userProfile: UserProfile = await apiClient.getProfile();

      // Store user profile in localStorage
      localStorage.setItem(USER_DATA_KEY, JSON.stringify(userProfile));

      // Update user state
      setUser(userProfile);

      // Return access code to display to user
      return registerResponse.access_code;
    } catch (err) {
      const axiosError = err as AxiosError<APIError>;
      const errorMessage = formatAPIError(axiosError.response?.data?.detail) || 'Registration failed. Please try again.';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const clearError = () => {
    setError(null);
  };

  const updateUser = useCallback((updatedUser: UserProfile | null) => {
    setUser(updatedUser);
    
    if (updatedUser) {
      localStorage.setItem(USER_DATA_KEY, JSON.stringify(updatedUser));
    } else {
      localStorage.removeItem(USER_DATA_KEY);
    }
  }, []);

  return (
    <AuthContext.Provider 
      value={{ 
        user, 
        isAuthenticated: !!user, 
        isLoading, 
        error, 
        login, 
        register, 
        logout, 
        clearError,
        updateUser 
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};