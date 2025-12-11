/**
 * API Client for Proxy Shop
 * Provides methods for authentication, user management, products, purchases, and payments
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import type {
  // Auth types
  RegisterRequest,
  RegisterResponse,
  LoginResponse,
  RefreshTokenResponse,
  TokenVerifyResponse,
  // User types
  UserProfile,
  UserHistoryResponse,
  ActivateCouponRequest,
  ActivateCouponResponse,
  ReferralsResponse,
  // Products types
  ProductsListResponse,
  CountryListItem,
  StateListItem,
  ProxyType,
  // Purchase types
  PurchaseRequest,
  PurchaseResponse,
  PurchaseHistoryResponse,
  ValidateProxyResponse,
  ExtendProxyRequest,
  ExtendProxyResponse,
  // Payment types
  CreatePaymentRequest,
  CreatePaymentResponse,
  TransactionHistoryResponse,
  // Error types
  APIError,
} from '@/types/api';
import {
  API_BASE_URL,
  API_TIMEOUT,
  ACCESS_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
} from './constants';

/**
 * Main API Client class
 * 
 * @remarks
 * Error Handling:
 * All API methods may throw AxiosError. When an error occurs, the error object
 * contains `response?.data` in the format of {@link APIError}.
 * 
 * Example error handling:
 * ```typescript
 * try {
 *   const result = await apiClient.login(accessCode);
 * } catch (error) {
 *   const axiosError = error as AxiosError<APIError>;
 *   const errorMessage = axiosError.response?.data.detail || 'Unknown error';
 *   const errorCode = axiosError.response?.data.error_code;
 *   console.error(errorMessage, errorCode);
 * }
 * ```
 */
class APIClient {
  private client: AxiosInstance;
  private isRefreshing: boolean = false;
  private refreshSubscribers: Array<(token: string) => void> = [];

  constructor() {
    // Initialize axios instance with base configuration
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Setup request interceptor for adding JWT token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem(ACCESS_TOKEN_KEY);
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Setup response interceptor for handling 401 errors and token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

        // Check if error is 401 and not from login or refresh endpoints
        if (
          error.response?.status === 401 &&
          originalRequest &&
          !originalRequest._retry &&
          !originalRequest.url?.includes('/auth/login') &&
          !originalRequest.url?.includes('/auth/refresh')
        ) {
          if (this.isRefreshing) {
            // If already refreshing, queue this request
            return new Promise((resolve) => {
              this.refreshSubscribers.push((token: string) => {
                if (originalRequest.headers) {
                  originalRequest.headers.Authorization = `Bearer ${token}`;
                }
                resolve(this.client(originalRequest));
              });
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
            if (!refreshToken) {
              throw new Error('No refresh token available');
            }

            // Attempt to refresh the token
            const response = await this.client.post<RefreshTokenResponse>(
              '/api/auth/refresh',
              { refresh_token: refreshToken }
            );

            const { access_token } = response.data;
            localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
            
            // Note: Backend currently returns only access_token in RefreshTokenResponse.
            // If backend schema changes to include refresh_token, uncomment the following:
            // if ('refresh_token' in response.data) {
            //   localStorage.setItem(REFRESH_TOKEN_KEY, (response.data as any).refresh_token);
            // }

            // Retry all queued requests with new token
            this.refreshSubscribers.forEach((callback) => callback(access_token));
            this.refreshSubscribers = [];
            this.isRefreshing = false;

            // Retry the original request
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${access_token}`;
            }
            return this.client(originalRequest);
          } catch (refreshError) {
            // Refresh failed, clear tokens and redirect to auth
            this.isRefreshing = false;
            this.refreshSubscribers = [];
            localStorage.removeItem(ACCESS_TOKEN_KEY);
            localStorage.removeItem(REFRESH_TOKEN_KEY);
            
            // Redirect to auth page
            if (typeof window !== 'undefined') {
              window.location.href = '/auth';
            }
            
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // ============================================================================
  // AUTHENTICATION METHODS
  // ============================================================================

  /**
   * Login with access code
   * @param accessCode - User's access code
   * @returns Login response with tokens and user data
   */
  async login(accessCode: string): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/api/auth/login', {
      access_code: accessCode,
    });
    return response.data;
  }

  /**
   * Register new user
   * @param data - Registration data
   * @returns Registration response with tokens
   */
  async register(data: RegisterRequest): Promise<RegisterResponse> {
    const response = await this.client.post<RegisterResponse>('/api/auth/register', data);
    return response.data;
  }

  /**
   * Refresh access token
   * @param refreshToken - Refresh token
   * @returns New access token (and optionally new refresh token if backend provides it)
   */
  async refreshToken(refreshToken: string): Promise<RefreshTokenResponse> {
    const response = await this.client.post<RefreshTokenResponse>('/api/auth/refresh', {
      refresh_token: refreshToken,
    });
    
    // Update access token in storage
    localStorage.setItem(ACCESS_TOKEN_KEY, response.data.access_token);
    
    // Note: Backend currently returns only access_token in RefreshTokenResponse.
    // If backend schema changes to include refresh_token, update storage:
    // if ('refresh_token' in response.data) {
    //   localStorage.setItem(REFRESH_TOKEN_KEY, (response.data as any).refresh_token);
    // }
    
    return response.data;
  }

  /**
   * Verify current token
   * @returns Token verification response
   */
  async verifyToken(): Promise<TokenVerifyResponse> {
    const response = await this.client.post<TokenVerifyResponse>('/api/auth/verify');
    return response.data;
  }

  // ============================================================================
  // USER METHODS
  // ============================================================================

  /**
   * Get current user profile
   * @returns User profile data
   */
  async getProfile(): Promise<UserProfile> {
    const response = await this.client.get<UserProfile>('/api/user/profile');
    return response.data;
  }

  /**
   * Get user action history
   * @param params - Query parameters for filtering and pagination
   * @returns User history with pagination
   */
  async getHistory(params?: {
    action_type?: string;
    page?: number;
    page_size?: number;
  }): Promise<UserHistoryResponse> {
    const response = await this.client.get<UserHistoryResponse>('/api/user/history', {
      params,
    });
    return response.data;
  }

  /**
   * Activate a coupon code
   * @param data - Coupon activation data
   * @returns Coupon activation response
   */
  async activateCoupon(data: ActivateCouponRequest): Promise<ActivateCouponResponse> {
    const response = await this.client.post<ActivateCouponResponse>(
      '/api/user/coupon/activate',
      data
    );
    return response.data;
  }

  /**
   * Get user referrals
   * @param userId - User ID
   * @param params - Query parameters for pagination
   * @returns Referrals list with pagination
   */
  async getReferrals(
    userId: number,
    params?: {
      page?: number;
      page_size?: number;
    }
  ): Promise<ReferralsResponse> {
    const response = await this.client.get<ReferralsResponse>(
      `/api/user/referrals/${userId}`,
      { params }
    );
    return response.data;
  }

  // ============================================================================
  // PAYMENT METHODS
  // ============================================================================

  /**
   * Generate Heleket payment address/invoice
   * @param data - Payment creation data
   * @returns Payment invoice details
   */
  async generateAddress(data: CreatePaymentRequest): Promise<CreatePaymentResponse> {
    const response = await this.client.post<CreatePaymentResponse>(
      '/api/payment/generate-address',
      data
    );
    return response.data;
  }

  /**
   * Get payment/transaction history
   * @param userId - User ID
   * @param params - Query parameters for pagination
   * @returns Transaction history with pagination
   */
  async getPaymentHistory(
    userId: number,
    params?: {
      page?: number;
      page_size?: number;
    }
  ): Promise<TransactionHistoryResponse> {
    const response = await this.client.get<TransactionHistoryResponse>(
      `/api/payment/history/${userId}`,
      { params }
    );
    return response.data;
  }

  // ============================================================================
  // PRODUCTS METHODS
  // ============================================================================

  /**
   * Get SOCKS5 products with filters
   * @param params - Query parameters for filtering and pagination
   * @returns Products list with pagination
   */
  async getSocks5Products(params?: {
    country?: string;
    state?: string;
    city?: string;
    zip?: string;
    random?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<ProductsListResponse> {
    const response = await this.client.get<ProductsListResponse>('/api/products/socks5', {
      params,
    });
    return response.data;
  }

  /**
   * Get PPTP products with filters
   * @param params - Query parameters for filtering and pagination
   * @returns Products list with pagination
   */
  async getPptpProducts(params?: {
    country?: string;
    state?: string;
    city?: string;
    zip?: string;
    random?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<ProductsListResponse> {
    const response = await this.client.get<ProductsListResponse>('/api/products/pptp', {
      params,
    });
    return response.data;
  }

  /**
   * Get available countries for proxy type
   * @param proxyType - Type of proxy (SOCKS5 or PPTP)
   * @returns List of countries with availability
   */
  async getCountries(proxyType: ProxyType): Promise<CountryListItem[]> {
    const response = await this.client.get<CountryListItem[]>('/api/products/countries', {
      params: { proxy_type: proxyType },
    });
    return response.data;
  }

  /**
   * Get available states for a country
   * @param country - Country name
   * @param proxyType - Type of proxy (SOCKS5 or PPTP)
   * @returns List of states with availability
   */
  async getStates(country: string, proxyType: ProxyType): Promise<StateListItem[]> {
    const response = await this.client.get<StateListItem[]>(
      `/api/products/states/${country}`,
      {
        params: { proxy_type: proxyType },
      }
    );
    return response.data;
  }

  // ============================================================================
  // PURCHASE METHODS
  // ============================================================================

  /**
   * Purchase SOCKS5 proxies
   * @param data - Purchase request data
   * @returns Purchase response with proxy details
   */
  async purchaseSocks5(data: PurchaseRequest): Promise<PurchaseResponse> {
    const response = await this.client.post<PurchaseResponse>('/api/purchase/socks5', data);
    return response.data;
  }

  /**
   * Purchase PPTP proxy
   * @param data - Purchase request data (without quantity)
   * @returns Purchase response with proxy details
   */
  async purchasePptp(
    data: Omit<PurchaseRequest, 'quantity'>
  ): Promise<PurchaseResponse> {
    const response = await this.client.post<PurchaseResponse>('/api/purchase/pptp', data);
    return response.data;
  }

  /**
   * Get purchase history
   * @param userId - User ID
   * @param params - Query parameters for filtering and pagination
   * @returns Purchase history with pagination
   */
  async getPurchaseHistory(
    userId: number,
    params?: {
      proxy_type?: ProxyType;
      page?: number;
      page_size?: number;
    }
  ): Promise<PurchaseHistoryResponse> {
    const response = await this.client.get<PurchaseHistoryResponse>(
      `/api/purchase/history/${userId}`,
      { params }
    );
    return response.data;
  }

  /**
   * Validate a proxy
   * @param proxyId - Proxy ID to validate (integer)
   * @param proxyType - Type of proxy (SOCKS5 or PPTP)
   * @returns Validation response with proxy status
   */
  async validateProxy(
    proxyId: number,
    proxyType: ProxyType
  ): Promise<ValidateProxyResponse> {
    const response = await this.client.post<ValidateProxyResponse>(
      `/api/purchase/validate/${proxyId}`,
      {},
      {
        params: { proxy_type: proxyType },
      }
    );
    return response.data;
  }

  /**
   * Extend proxy duration
   * @param proxyId - Proxy ID to extend (integer)
   * @param proxyType - Type of proxy (SOCKS5 or PPTP)
   * @param data - Extension request data
   * @returns Extension response with new expiration
   */
  async extendProxy(
    proxyId: number,
    proxyType: ProxyType,
    data: ExtendProxyRequest
  ): Promise<ExtendProxyResponse> {
    const response = await this.client.post<ExtendProxyResponse>(
      `/api/purchase/extend/${proxyId}`,
      data,
      {
        params: { proxy_type: proxyType },
      }
    );
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new APIClient();

