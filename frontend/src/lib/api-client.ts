/**
 * Type-safe HTTP client for backend API
 * Handles authentication, token refresh, and all API endpoints
 *
 * Note: Tokens are stored in regular cookies and Zustand state.
 * The client automatically adds Authorization header from state.
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import type {
  // Auth types
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  RefreshTokenRequest,
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
  // Payment types (Heleket)
  CreatePaymentRequest,
  CreatePaymentResponse,
  TransactionHistoryResponse,
  // Error type
  APIError
} from '@/types/api';
import { API_BASE_URL } from './constants';

/**
 * Main API client class
 * Handles all HTTP communication with backend
 */
class APIClient {
  private client: AxiosInstance;
  private isRefreshing: boolean = false;
  private refreshSubscribers: Array<() => void> = [];

  constructor() {
    // Create axios instance with base configuration
    // Use relative URLs - Nginx proxies /api/* to backend
    this.client = axios.create({
      baseURL: '',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // Request interceptor: Add Authorization header from Zustand store
    this.client.interceptors.request.use(
      (config) => {
        // Import store dynamically to avoid circular dependency
        if (typeof window !== 'undefined') {
          const { useAuthStore } = require('@/store/auth-store');
          const token = useAuthStore.getState().accessToken;

          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
          }
        }

        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor: handle 401 and auto-refresh tokens
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

        // If 401 and not already retried, attempt token refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
          // Skip refresh for auth endpoints
          if (originalRequest.url?.includes('/auth/refresh') || originalRequest.url?.includes('/auth/login')) {
            return Promise.reject(error);
          }

          if (this.isRefreshing) {
            // Queue request until refresh completes
            return new Promise((resolve) => {
              this.refreshSubscribers.push(() => {
                resolve(this.client(originalRequest));
              });
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            // Import store dynamically
            const { useAuthStore } = require('@/store/auth-store');
            const refreshToken = useAuthStore.getState().refreshToken;

            if (!refreshToken) {
              throw new Error('No refresh token available');
            }

            // Call refresh endpoint with refresh token
            const response = await axios.post('/api/auth/refresh', {
              refresh_token: refreshToken
            });

            const { access_token } = response.data;

            // Update tokens in store
            useAuthStore.getState().setTokens(access_token, refreshToken);

            // Update Authorization header for retry
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${access_token}`;
            }

            // Retry all queued requests
            this.refreshSubscribers.forEach((callback) => callback());
            this.refreshSubscribers = [];

            // Retry original request
            return this.client(originalRequest);
          } catch (refreshError) {
            // Refresh failed, logout user
            if (typeof window !== 'undefined') {
              const { useAuthStore } = require('@/store/auth-store');
              useAuthStore.getState().logout();
            }
            return Promise.reject(refreshError);
          } finally {
            this.isRefreshing = false;
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // ============================================
  // Auth Methods
  // ============================================

  /**
   * Login with access code
   * POST /api/auth/login
   */
  async login(accessCode: string): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/api/auth/login', {
      access_code: accessCode
    });
    return response.data;
  }

  /**
   * Register new user
   * POST /api/auth/register
   */
  async register(data: RegisterRequest): Promise<RegisterResponse> {
    const response = await this.client.post<RegisterResponse>('/api/auth/register', data);
    return response.data;
  }

  /**
   * Refresh access token
   * POST /api/auth/refresh
   */
  async refreshToken(refreshToken: string): Promise<RefreshTokenResponse> {
    const response = await this.client.post<RefreshTokenResponse>('/api/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  }

  /**
   * Verify access token
   * POST /api/auth/verify
   */
  async verifyToken(): Promise<TokenVerifyResponse> {
    const response = await this.client.post<TokenVerifyResponse>('/api/auth/verify');
    return response.data;
  }

  // ============================================
  // User Methods
  // ============================================

  /**
   * Get user profile
   * GET /api/user/profile
   */
  async getProfile(): Promise<UserProfile> {
    const response = await this.client.get<UserProfile>('/api/user/profile');
    return response.data;
  }

  /**
   * Get user history
   * GET /api/user/history
   */
  async getHistory(params: { 
    action_type?: string; 
    page?: number; 
    page_size?: number;
  }): Promise<UserHistoryResponse> {
    const response = await this.client.get<UserHistoryResponse>('/api/user/history', { params });
    return response.data;
  }

  /**
   * Activate coupon
   * POST /api/user/coupon/activate
   */
  async activateCoupon(data: ActivateCouponRequest): Promise<ActivateCouponResponse> {
    const response = await this.client.post<ActivateCouponResponse>('/api/user/coupon/activate', data);
    return response.data;
  }

  /**
   * Get user referrals
   * GET /api/user/referrals/{userId}
   */
  async getReferrals(
    userId: number, 
    params: { page?: number; page_size?: number }
  ): Promise<ReferralsResponse> {
    const response = await this.client.get<ReferralsResponse>(`/api/user/referrals/${userId}`, { params });
    return response.data;
  }

  // ============================================
  // Payment Methods
  // ============================================

  /**
   * Create a Heleket payment invoice with universal payment link (Mode B)
   * POST /api/payment/generate-address
   */
  async generateAddress(data: CreatePaymentRequest): Promise<CreatePaymentResponse> {
    const response = await this.client.post<CreatePaymentResponse>('/api/payment/generate-address', data);
    return response.data;
  }

  /**
   * Get payment history
   * GET /api/payment/history/{userId}
   */
  async getPaymentHistory(
    userId: number, 
    params: { page?: number; page_size?: number }
  ): Promise<TransactionHistoryResponse> {
    const response = await this.client.get<TransactionHistoryResponse>(`/api/payment/history/${userId}`, { params });
    return response.data;
  }

  // ============================================
  // Products Methods
  // ============================================

  /**
   * Get SOCKS5 products
   * GET /api/products/socks5
   */
  async getSocks5Products(params: {
    country: string;
    state?: string;
    city?: string;
    zip?: string;
    random?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<ProductsListResponse> {
    const response = await this.client.get<ProductsListResponse>('/api/products/socks5', { params });
    return response.data;
  }

  /**
   * Get PPTP products
   * GET /api/products/pptp
   */
  async getPptpProducts(params: {
    country: string;
    state?: string;
    city?: string;
    zip?: string;
    random?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<ProductsListResponse> {
    const response = await this.client.get<ProductsListResponse>('/api/products/pptp', { params });
    return response.data;
  }

  /**
   * Get available countries
   * GET /api/products/countries
   */
  async getCountries(proxyType: ProxyType): Promise<CountryListItem[]> {
    const response = await this.client.get<CountryListItem[]>('/api/products/countries', {
      params: { proxy_type: proxyType }
    });
    return response.data;
  }

  /**
   * Get available states for country
   * GET /api/products/states/{country}
   */
  async getStates(country: string, proxyType: ProxyType): Promise<StateListItem[]> {
    const response = await this.client.get<StateListItem[]>(`/api/products/states/${country}`, {
      params: { proxy_type: proxyType }
    });
    return response.data;
  }

  // ============================================
  // Purchase Methods
  // ============================================

  /**
   * Purchase SOCKS5 proxy
   * POST /api/purchase/socks5
   */
  async purchaseSocks5(data: PurchaseRequest): Promise<PurchaseResponse> {
    const response = await this.client.post<PurchaseResponse>('/api/purchase/socks5', data);
    return response.data;
  }

  /**
   * Purchase PPTP proxy
   * POST /api/purchase/pptp
   */
  async purchasePptp(data: Omit<PurchaseRequest, 'quantity'>): Promise<PurchaseResponse> {
    const response = await this.client.post<PurchaseResponse>('/api/purchase/pptp', data);
    return response.data;
  }

  /**
   * Get purchase history
   * GET /api/purchase/history/{userId}
   */
  async getPurchaseHistory(
    userId: number,
    params: { proxy_type?: ProxyType; page?: number; page_size?: number }
  ): Promise<PurchaseHistoryResponse> {
    const response = await this.client.get<PurchaseHistoryResponse>(`/api/purchase/history/${userId}`, { params });
    return response.data;
  }

  /**
   * Validate proxy status
   * POST /api/purchase/validate/{proxyId}
   */
  async validateProxy(proxyId: number, proxyType: ProxyType): Promise<ValidateProxyResponse> {
    const response = await this.client.post<ValidateProxyResponse>(
      `/api/purchase/validate/${proxyId}`,
      {},
      { params: { proxy_type: proxyType } }
    );
    return response.data;
  }

  /**
   * Extend proxy duration
   * POST /api/purchase/extend/{proxyId}
   */
  async extendProxy(
    proxyId: number,
    proxyType: ProxyType,
    data: ExtendProxyRequest
  ): Promise<ExtendProxyResponse> {
    const response = await this.client.post<ExtendProxyResponse>(
      `/api/purchase/extend/${proxyId}`,
      data,
      { params: { proxy_type: proxyType } }
    );
    return response.data;
  }

  // ============================================
  // External Proxy Methods
  // ============================================

  /**
   * Get list of external SOCKS5 proxies
   * GET /api/external-proxy/list
   */
  async getExternalProxies(params?: {
    country_code?: string;
    city?: string;
    page?: number;
    page_size?: number;
  }): Promise<any> {
    const response = await this.client.get('/api/external-proxy/list', { params });
    return response.data;
  }

  /**
   * Purchase external SOCKS5 proxy
   * POST /api/external-proxy/purchase
   */
  async purchaseExternalProxy(data: { product_id: number }): Promise<any> {
    const response = await this.client.post('/api/external-proxy/purchase', data);
    return response.data;
  }

  /**
   * Refund external proxy
   * POST /api/external-proxy/refund
   */
  async refundExternalProxy(data: { order_id: string }): Promise<any> {
    const response = await this.client.post('/api/external-proxy/refund', data);
    return response.data;
  }

  /**
   * Sync external proxies (admin only)
   * POST /api/external-proxy/sync
   */
  async syncExternalProxies(data?: {
    country_code?: string;
    city?: string;
    region?: string;
    page_size?: number;
  }): Promise<any> {
    const response = await this.client.post('/api/external-proxy/sync', data);
    return response.data;
  }

  /**
   * Get external proxy stats (admin only)
   * GET /api/external-proxy/stats
   */
  async getExternalProxyStats(): Promise<any> {
    const response = await this.client.get('/api/external-proxy/stats');
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new APIClient();

