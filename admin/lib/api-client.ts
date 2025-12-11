/**
 * Admin API Client for Proxy Shop Admin Panel
 * Provides methods for dashboard stats, user management, coupons, and proxy inventory
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import { API_BASE_URL } from '../constants';

// API timeout (2 minutes)
const API_TIMEOUT = 120000;

// LocalStorage keys for JWT tokens
const ACCESS_TOKEN_KEY = 'admin_access_token';
const REFRESH_TOKEN_KEY = 'admin_refresh_token';

/**
 * Response type for the login endpoint
 */
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  is_admin: boolean;
  user?: {
    id: number;
    telegram_id: number;
    username?: string;
    language?: string;
  };
}

/**
 * Admin API Client class
 *
 * @remarks
 * Error Handling:
 * All API methods may throw AxiosError. When an error occurs, the error object
 * contains `response?.data` with error details.
 *
 * Example error handling:
 * ```typescript
 * try {
 *   const stats = await adminApiClient.getDashboardStats();
 * } catch (error) {
 *   const axiosError = error as AxiosError<any>;
 *   const errorMessage = axiosError.response?.data.detail || 'Unknown error';
 *   console.error(errorMessage);
 * }
 * ```
 */
class AdminAPIClient {
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
            const response = await this.client.post<{ access_token: string }>(
              '/api/auth/refresh',
              { refresh_token: refreshToken }
            );

            const { access_token } = response.data;
            localStorage.setItem(ACCESS_TOKEN_KEY, access_token);

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
              window.location.href = '/';
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
   * Login with access code (admin must have is_admin=True)
   * @param accessCode - Admin access code
   * @returns Login response with tokens and user data
   * @throws {AxiosError} Status 401 for invalid credentials
   * @throws {AxiosError} Status 403 for non-admin users
   * @throws {Error} Protocol error if is_admin field is missing or invalid
   */
  async login(accessCode: string): Promise<LoginResponse> {
    try {
      const response = await this.client.post<LoginResponse>('/api/auth/login', {
        access_code: accessCode,
      });

      // Strict validation: is_admin must be explicitly true
      if (response.data.is_admin === true) {
        // Store tokens only if admin
        if (response.data.access_token) {
          localStorage.setItem(ACCESS_TOKEN_KEY, response.data.access_token);
        }
        if (response.data.refresh_token) {
          localStorage.setItem(REFRESH_TOKEN_KEY, response.data.refresh_token);
        }

        return response.data;
      }

      // Clear any tokens that might have been set
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);

      // Check if is_admin is explicitly false (not admin)
      if (response.data.is_admin === false) {
        console.warn('Login attempt by non-admin user');
        
        // Create proper AxiosError-compatible error
        const axiosError = new Error('Admin access required') as AxiosError;
        axiosError.isAxiosError = true;
        axiosError.name = 'AxiosError';
        axiosError.config = response.config;
        axiosError.request = response.request;
        axiosError.response = {
          ...response,
          status: 403,
          statusText: 'Forbidden',
          data: { detail: 'Admin access required' },
        };
        axiosError.toJSON = () => ({
          message: axiosError.message,
          name: axiosError.name,
          stack: axiosError.stack,
          config: axiosError.config,
        });
        
        throw axiosError;
      }

      // Protocol error: is_admin field is missing or has unexpected value
      console.error('Protocol error: is_admin field is missing or invalid', {
        is_admin: response.data.is_admin,
        response_data: response.data,
      });

      const protocolError = new Error('Protocol error: invalid or missing is_admin field in API response') as AxiosError;
      protocolError.isAxiosError = true;
      protocolError.name = 'AxiosError';
      protocolError.config = response.config;
      protocolError.request = response.request;
      protocolError.response = {
        ...response,
        status: 500,
        statusText: 'Internal Server Error',
        data: { detail: 'Protocol error: invalid API response format' },
      };
      protocolError.toJSON = () => ({
        message: protocolError.message,
        name: protocolError.name,
        stack: protocolError.stack,
        config: protocolError.config,
      });

      throw protocolError;
    } catch (error) {
      // Clear tokens on any error
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      throw error;
    }
  }

  /**
   * Logout and clear tokens
   */
  logout(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!localStorage.getItem(ACCESS_TOKEN_KEY);
  }

  /**
   * Validate current token by making a lightweight request to backend
   * @returns true if token is valid, false otherwise
   */
  async validateToken(): Promise<boolean> {
    try {
      // Use a lightweight admin endpoint to validate token
      await this.client.get('/api/admin/stats');
      return true;
    } catch (error) {
      const axiosError = error as AxiosError;
      
      // If 401 or 403, token is invalid
      if (axiosError.response?.status === 401 || axiosError.response?.status === 403) {
        console.warn('Token validation failed: invalid or expired token');
        this.logout();
        return false;
      }
      
      // For other errors (network, server error), assume token might still be valid
      console.error('Token validation error:', error);
      return true;
    }
  }

  // ============================================================================
  // DASHBOARD METHODS
  // ============================================================================

  /**
   * Get dashboard statistics
   * @returns Dashboard stats including total users, revenue, purchases, etc.
   */
  async getDashboardStats(): Promise<any> {
    const response = await this.client.get('/api/admin/stats');
    return response.data;
  }

  /**
   * Get revenue chart data
   * @param period - Period for chart (7d, 30d, etc.)
   * @returns Revenue chart data points
   */
  async getRevenueChart(period: string = '30d'): Promise<any[]> {
    const response = await this.client.get('/api/admin/revenue-chart', {
      params: { period }
    });
    return response.data;
  }

  /**
   * Get recent activity log
   * @param limit - Maximum number of activities to return (default: 20)
   * @returns Recent activity log entries
   */
  async getRecentActivity(limit: number = 20): Promise<any[]> {
    const response = await this.client.get('/api/admin/activity-log', {
      params: { limit }
    });
    return response.data;
  }

  // ============================================================================
  // USER MANAGEMENT METHODS
  // ============================================================================

  /**
   * Get users list with filters and pagination
   * @param params - Query parameters
   * @returns Paginated users list
   */
  async getUsers(params?: {
    search?: string;
    platform?: string;
    date_from?: string;
    date_to?: string;
    min_balance?: number;
    max_balance?: number;
    is_blocked?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<any> {
    const response = await this.client.get('/api/admin/users', { params });
    return response.data;
  }

  /**
   * Get user details
   * @param userId - User ID
   * @returns User details
   */
  async getUserDetails(userId: number): Promise<any> {
    const response = await this.client.get(`/api/admin/users/${userId}`);
    return response.data;
  }

  /**
   * Update user
   * @param userId - User ID
   * @param data - Update data
   * @returns Updated user
   */
  async updateUser(userId: number, data: {
    balance?: number;
    is_blocked?: boolean;
    blocked_reason?: string;
    language?: string;
  }): Promise<any> {
    const response = await this.client.patch(`/api/admin/users/${userId}`, data);
    return response.data;
  }

  /**
   * Get top users
   * @param params - Query parameters
   * @returns Top users list
   */
  async getTopUsers(params?: {
    metric?: 'spent' | 'purchases' | 'balance';
    limit?: number;
  }): Promise<any[]> {
    const response = await this.client.get('/api/admin/top-users', { params });
    return response.data;
  }

  // ============================================================================
  // COUPON MANAGEMENT METHODS
  // ============================================================================

  /**
   * Get coupons list with filters and pagination
   * @param params - Query parameters
   * @returns Paginated coupons list
   */
  async getCoupons(params?: {
    search?: string;
    is_active?: boolean;
    date_from?: string;
    date_to?: string;
    page?: number;
    page_size?: number;
  }): Promise<any> {
    const response = await this.client.get('/api/admin/coupons', { params });
    return response.data;
  }

  /**
   * Create new coupon
   * @param data - Coupon data
   * @returns Created coupon
   */
  async createCoupon(data: {
    code: string;
    discount_percent: number;
    max_uses: number;
    expires_at?: string;
    is_active?: boolean;
  }): Promise<any> {
    const response = await this.client.post('/api/admin/coupons', data);
    return response.data;
  }

  /**
   * Update coupon
   * @param couponId - Coupon ID
   * @param data - Update data
   * @returns Updated coupon
   */
  async updateCoupon(couponId: number, data: {
    discount_percent?: number;
    max_uses?: number;
    is_active?: boolean;
    expires_at?: string;
  }): Promise<any> {
    const response = await this.client.patch(`/api/admin/coupons/${couponId}`, data);
    return response.data;
  }

  /**
   * Delete coupon
   * @param couponId - Coupon ID
   */
  async deleteCoupon(couponId: number): Promise<void> {
    await this.client.delete(`/api/admin/coupons/${couponId}`);
  }

  // ============================================================================
  // PROXY INVENTORY METHODS
  // ============================================================================

  /**
   * Get proxies inventory with filters and pagination
   * @param params - Query parameters
   * @returns Paginated proxies list
   */
  async getProxies(params?: {
    country?: string;
    state?: string;
    city?: string;
    is_available?: boolean;
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<any> {
    const response = await this.client.get('/api/admin/proxies', { params });
    return response.data;
  }

  /**
   * Add single proxy
   * @param data - Proxy data
   * @returns Created proxy
   */
  async addProxy(data: {
    ip: string;
    port: number;
    country: string;
    state?: string;
    city?: string;
    price_per_hour: number;
    notes?: string;
  }): Promise<any> {
    const response = await this.client.post('/api/admin/proxies', data);
    return response.data;
  }

  /**
   * Bulk upload proxies
   * @param proxies - Array of proxies
   * @returns Bulk upload result
   */
  async bulkUploadProxies(proxies: Array<{
    ip: string;
    port: number;
    country: string;
    state?: string;
    city?: string;
    price_per_hour: number;
    notes?: string;
  }>): Promise<any> {
    const response = await this.client.post('/api/admin/proxies/bulk', { proxies });
    return response.data;
  }

  /**
   * Get proxy statistics
   * @returns Proxy inventory statistics
   */
  async getProxyStats(): Promise<any> {
    const response = await this.client.get('/api/admin/proxies/stats');
    return response.data;
  }

  /**
   * Update proxy availability
   * @param proxyId - Proxy ID
   * @param data - Update data
   * @returns Updated proxy
   */
  async updateProxyAvailability(proxyId: number, data: {
    is_available: boolean;
    price_per_hour?: number;
    notes?: string;
  }): Promise<any> {
    const response = await this.client.patch(`/api/admin/proxies/${proxyId}`, data);
    return response.data;
  }

  /**
   * Delete proxy
   * @param proxyId - Proxy ID
   */
  async deleteProxy(proxyId: number): Promise<void> {
    await this.client.delete(`/api/admin/proxies/${proxyId}`);
  }

  // ============================================================================
  // PPTP BULK UPLOAD METHODS
  // ============================================================================

  /**
   * Bulk upload PPTP proxies
   * @param data - Proxy data string in line or CSV format
   * @param format - Format type ('line' or 'csv' or 'auto')
   * @returns Bulk upload result with created/failed counts
   */
  async bulkUploadPPTP(
    data: string,
    format?: string,
    catalogId?: number,
    catalogName?: string,
    catalogPrice?: number
  ): Promise<any> {
    const response = await this.client.post('/api/admin/pptp/bulk', {
      data,
      format: format === 'auto' ? undefined : format,
      catalog_id: catalogId,
      catalog_name: catalogName,
      catalog_price: catalogPrice
    });
    return response.data;
  }

  /**
   * Get PPTP proxies list with pagination
   * @param page - Page number (default: 1)
   * @param pageSize - Items per page (default: 50)
   * @param search - Optional search query
   * @returns Paginated list of PPTP proxies
   */
  async getPptpProxies(page: number = 1, pageSize: number = 50, search?: string, catalogId?: number): Promise<any> {
    const params: any = { page, page_size: pageSize };
    if (search) {
      params.search = search;
    }
    if (catalogId) {
      params.catalog_id = catalogId;
    }
    const response = await this.client.get('/api/admin/pptp', { params });
    return response.data;
  }

  /**
   * Get list of PPTP catalogs/groups
   * @param proxyType - Proxy type (default: 'PPTP')
   * @returns List of catalogs with id, name, price
   */
  async getCatalogs(proxyType: string = 'PPTP'): Promise<any> {
    const response = await this.client.get('/api/admin/catalogs', {
      params: { proxy_type: proxyType }
    });
    return response.data;
  }

  /**
   * Update catalog details
   * @param catalogId - Catalog ID to update
   * @param data - Update data (line_name, price, description_ru, description_eng)
   * @returns Updated catalog data
   */
  async updateCatalog(catalogId: number, data: {
    line_name?: string;
    price?: number;
    description_ru?: string;
    description_eng?: string;
  }): Promise<any> {
    const response = await this.client.patch(`/api/admin/catalogs/${catalogId}`, data);
    return response.data;
  }

  /**
   * Delete catalog and all its proxies
   * @param catalogId - Catalog ID to delete
   */
  async deleteCatalog(catalogId: number): Promise<void> {
    await this.client.delete(`/api/admin/catalogs/${catalogId}`);
  }

  /**
   * Delete single PPTP proxy
   * @param productId - Product ID to delete
   */
  async deletePptpProxy(productId: number): Promise<void> {
    await this.client.delete(`/api/admin/pptp/${productId}`);
  }

  /**
   * Bulk delete PPTP proxies
   * @param productIds - Array of product IDs to delete
   * @returns Bulk delete result with deleted/failed counts
   */
  async bulkDeletePptp(productIds: number[]): Promise<any> {
    const response = await this.client.post('/api/admin/pptp/bulk-delete', {
      product_ids: productIds
    });
    return response.data;
  }

  // ============================================================================
  // BROADCAST METHODS
  // ============================================================================

  /**
   * Create and start a broadcast message
   * @param messageText - Message text (HTML supported)
   * @param messagePhoto - Optional photo URL or file_id
   * @param filterLanguage - Optional language filter (ru or en)
   * @returns Broadcast details and status
   */
  async createBroadcast(
    messageText: string,
    messagePhoto?: string,
    filterLanguage?: string
  ): Promise<any> {
    const response = await this.client.post('/api/admin/broadcast', {
      message_text: messageText,
      message_photo: messagePhoto || null,
      filter_language: filterLanguage || null
    });
    return response.data;
  }

  /**
   * Get list of broadcasts with pagination
   * @param limit - Number of broadcasts to return (default: 20)
   * @param offset - Offset for pagination (default: 0)
   * @returns List of broadcasts
   */
  async getBroadcasts(limit: number = 20, offset: number = 0): Promise<any> {
    const response = await this.client.get('/api/admin/broadcast', {
      params: { limit, offset }
    });
    return response.data;
  }

  /**
   * Get broadcast status by ID
   * @param broadcastId - Broadcast ID
   * @returns Broadcast status and progress
   */
  async getBroadcastStatus(broadcastId: number): Promise<any> {
    const response = await this.client.get(`/api/admin/broadcast/${broadcastId}`);
    return response.data;
  }

  /**
   * Cancel a running or pending broadcast
   * @param broadcastId - Broadcast ID
   * @returns Success status
   */
  async cancelBroadcast(broadcastId: number): Promise<any> {
    const response = await this.client.post(`/api/admin/broadcast/${broadcastId}/cancel`);
    return response.data;
  }

  /**
   * Send a test broadcast message to your own Telegram
   * @param messageText - Message text (HTML supported)
   * @param messagePhoto - Optional photo URL or file_id
   * @returns Success status
   */
  async sendTestBroadcast(messageText: string, messagePhoto?: string): Promise<any> {
    const response = await this.client.post('/api/admin/broadcast/test', {
      message_text: messageText,
      message_photo: messagePhoto || null
    });
    return response.data;
  }
}

// Export singleton instance
export const adminApiClient = new AdminAPIClient();

// Export token keys for direct access if needed
export { ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY };
