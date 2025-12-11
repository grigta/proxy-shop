/**
 * Application constants and configuration
 */

// ============================================================================
// API CONFIGURATION
// ============================================================================

/**
 * Base URL for backend API
 */
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Base URL for web application
 */
export const APP_BASE_URL = import.meta.env.VITE_APP_URL || 'http://localhost:3000';

// ============================================================================
// TOKEN CONFIGURATION
// ============================================================================

/**
 * LocalStorage key for access token
 */
export const ACCESS_TOKEN_KEY = 'access_token';

/**
 * LocalStorage key for refresh token
 */
export const REFRESH_TOKEN_KEY = 'refresh_token';

/**
 * LocalStorage key for user data
 */
export const USER_DATA_KEY = 'user_data';

// ============================================================================
// API TIMEOUTS
// ============================================================================

/**
 * Timeout for API requests (30 seconds)
 */
export const API_TIMEOUT = 30000;

// ============================================================================
// PAGINATION DEFAULTS
// ============================================================================

/**
 * Default page size for paginated requests
 */
export const DEFAULT_PAGE_SIZE = 10;

/**
 * Maximum page size for paginated requests
 */
export const MAX_PAGE_SIZE = 100;

// ============================================================================
// PROXY CONFIGURATION
// ============================================================================

/**
 * Available proxy types
 */
export const PROXY_TYPES = {
  SOCKS5: 'SOCKS5',
  PPTP: 'PPTP'
} as const;

/**
 * Default proxy duration in hours
 */
export const DEFAULT_PROXY_DURATION_HOURS = 24;

// ============================================================================
// PAYMENT CONFIGURATION
// ============================================================================

/**
 * Minimum deposit amount in USD
 */
export const MIN_DEPOSIT_USD = 10;

