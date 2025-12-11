/**
 * TypeScript types generated from backend Pydantic schemas
 * All types correspond exactly to backend API response/request models
 */

// ============================================
// Enums
// ============================================

export enum PlatformType {
  TELEGRAM = 'telegram',
  WEB = 'web'
}

export enum ProxyType {
  SOCKS5 = 'SOCKS5',
  PPTP = 'PPTP'
}

/**
 * @deprecated Use Heleket universal payment links instead. This enum is for legacy cryptocurrencyapi.net integration only.
 */
export enum CryptoChain {
  BTC = 'BTC',
  ETH = 'ETH',
  LTC = 'LTC',
  BNB = 'BNB',
  USDT_TRC20 = 'USDT_TRC20',
  USDT_ERC20 = 'USDT_ERC20',
  USDT_BEP20 = 'USDT_BEP20'
}

// ============================================
// Payment Types (Heleket Integration - Mode B)
// ============================================

/**
 * Request to create Heleket payment invoice
 * Optional amount in USD - if not provided, MIN_DEPOSIT_USD is used
 */
export interface CreatePaymentRequest {
  amount_usd?: string; // Decimal fields are strings in JSON
}

/**
 * Response from Heleket payment invoice creation
 * Contains universal payment link for user to complete payment
 */
export interface CreatePaymentResponse {
  payment_url: string; // Universal payment link for user to complete payment
  payment_uuid: string; // Unique Heleket payment identifier
  order_id: string; // Order identifier for tracking (format: DEPOSIT-{user_id}-{timestamp})
  expired_at: string | null; // Payment expiration timestamp in ISO format
  amount_usd: string; // Invoice amount in USD
  min_amount_usd: string; // Global minimum deposit amount in USD
}

// ============================================
// Auth Types (from backend/schemas/auth.py)
// ============================================

export interface LoginRequest {
  access_code: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: number;
  access_code: string;
  platform_registered: PlatformType;
  balance: string; // Decimal fields are strings in JSON
  telegram_id: number | null;
}

export interface RegisterRequest {
  platform: PlatformType;
  language: string;
  telegram_id?: number;
  username?: string;
  referral_code?: string;
}

export interface RegisterResponse {
  access_code: string;
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: number;
  platform: PlatformType;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
}

export interface TokenVerifyResponse {
  valid: boolean;
  user_id: number | null;
  access_code: string | null;
  expires_at: string | null;
}

// ============================================
// User Types (from backend/schemas/user.py)
// ============================================

/**
 * User profile with all account information
 * Includes balance, referral data, and statistics
 */
export interface UserProfile {
  user_id: number;
  access_code: string;
  balance: string;
  datestamp: string;
  platform_registered: PlatformType;
  language: string;
  username: string | null;
  telegram_id: number | null;
  referral_link_bot: string;
  referral_link_web: string;
  myreferal_id: string;
  referal_quantity: number;
  total_earned_from_referrals: string;
}

/**
 * Single entry in user action history
 * Formatted message ready for display
 */
export interface UserHistoryItem {
  id_log: number;
  action_type: string;
  action_description: string;
  date_of_action: string;
  formatted_message: string;
}

export interface UserHistoryResponse {
  history: UserHistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Referral user statistics
 */
export interface ReferralItem {
  user_id: number;
  username: string | null;
  datestamp: string;
  total_spent: string;
  bonus_earned: string;
  is_active: boolean;
}

export interface ReferralsResponse {
  referrals: ReferralItem[];
  total_referrals: number;
  total_earned: string;
  referral_bonus_percentage: number;
  page: number;
  page_size: number;
}

export interface ActivateCouponRequest {
  coupon_code: string;
}

export interface ActivateCouponResponse {
  success: boolean;
  message: string;
  coupon_code: string;
  discount_percentage: string;
  discount_amount: string | null;
  expires_at: string | null;
  usage_info: string;
}

// ============================================
// Products Types (from backend/schemas/products.py)
// ============================================

/**
 * Single proxy item in catalog
 * Contains all proxy details including location and ISP info
 */
export interface ProxyItem {
  product_id: number;
  ip: string;
  port: string | null;
  login: string | null;
  password: string | null;
  country: string;
  state: string | null;
  city: string | null;
  zip: string | null;
  ISP: string | null;
  ORG: string | null;
  speed: string | null;
  price: string;
  datestamp: string;
}

/**
 * Paginated list of proxy products
 * Includes filters and pagination info
 */
export interface ProductsListResponse {
  products: ProxyItem[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
  filters: Record<string, string | null>;
}

export interface CountryListItem {
  country: string;
  country_code: string;
  flag: string;
  available_count: number;
}

export interface StateListItem {
  state: string;
  available_count: number;
}

// ============================================
// Purchase Types (from backend/schemas/purchase.py)
// ============================================

export interface PurchaseRequest {
  product_id: number;
  quantity: number;
  coupon_code?: string;
}

/**
 * Response after successful proxy purchase
 * Includes purchased proxy details and updated balance
 */
export interface PurchaseResponse {
  success: boolean;
  order_id: string | null;
  product_id: number;
  quantity: number;
  price: string;
  original_price: string;
  discount_applied: string | null;
  country: string;
  state: string | null;
  city: string | null;
  zip: string | null;
  proxies: Array<Record<string, any>>;
  expires_at: string;
  hours_left: number;
  new_balance: string;
}

/**
 * Single purchase entry in history
 * Contains proxy data and expiration info
 */
export interface PurchaseHistoryItem {
  id: number;
  order_id: string | null; // Only for SOCKS5
  proxy_type: ProxyType;
  quantity: number;
  price: string;
  country: string;
  state: string | null;
  city: string | null;
  zip: string | null;
  proxies: Array<Record<string, any>>;
  datestamp: string;
  expires_at: string;
  hours_left: number;
  isRefunded: boolean;
}

export interface PurchaseHistoryResponse {
  purchases: PurchaseHistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Proxy validation result
 * Message is pre-formatted in Russian
 */
export interface ValidateProxyResponse {
  proxy_id: number;
  online: boolean;
  latency_ms: number | null;
  exit_ip: string | null;
  minutes_since_purchase: number;
  refund_eligible: boolean;
  refund_window_minutes: number;
  message: string; // Pre-formatted message in Russian
}

export interface ExtendProxyRequest {
  hours: number;
}

export interface ExtendProxyResponse {
  success: boolean;
  proxy_id: number;
  price: string;
  new_expires_at: string;
  hours_added: number;
  new_balance: string;
  message: string; // Pre-formatted message in Russian
}

// ============================================
// Payment Types (Legacy - from backend/schemas/payment.py)
// ============================================

/**
 * @deprecated Use CreatePaymentRequest instead. This interface is for legacy cryptocurrencyapi.net integration only.
 */
export interface GenerateAddressRequest {
  chain: CryptoChain;
}

/**
 * Generated cryptocurrency deposit address
 * QR code is in base64 data URI format
 * @deprecated Use CreatePaymentResponse instead. This interface is for legacy cryptocurrencyapi.net integration only.
 */
export interface GenerateAddressResponse {
  address: string;
  chain: CryptoChain;
  qr_code: string; // Format: "data:image/png;base64,..."
  valid_until: string | null; // For USDT_TRC20
  min_amount_usd: string;
  network_name: string;
}

/**
 * Transaction history item
 * Contains cryptocurrency transaction details
 */
export interface TransactionHistoryItem {
  id_tranz: number;
  chain: string;
  currency: string;
  amount_in_dollar: string;
  coin_amount: string;
  coin_course: string;
  txid: string;
  from_address: string;
  to_address: string;
  fee: string;
  dateOfTransaction: string;
  confirmation: number | null;
}

export interface TransactionHistoryResponse {
  transactions: TransactionHistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

// ============================================
// Error Types
// ============================================

/**
 * Standard API error response
 */
export interface APIError {
  detail: string;
  error_code?: string;
  status_code?: number;
}

