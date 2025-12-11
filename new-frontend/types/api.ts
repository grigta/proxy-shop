/**
 * TypeScript types for Proxy Shop API
 * Based on backend Pydantic schemas
 */

// ============================================================================
// ENUM TYPES
// ============================================================================

/**
 * Platform type for user registration
 */
export enum PlatformType {
  TELEGRAM = 'telegram',
  WEB = 'web'
}

/**
 * Proxy type
 */
export enum ProxyType {
  SOCKS5 = 'SOCKS5',
  PPTP = 'PPTP'
}

// ============================================================================
// AUTH TYPES
// ============================================================================

/**
 * Request body for user registration
 */
export interface RegisterRequest {
  platform: PlatformType;
  language: string;
  telegram_id?: number;
  username?: string;
  referral_code?: string;
}

/**
 * Response from user registration
 */
export interface RegisterResponse {
  access_code: string;
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: number;
  platform: PlatformType;
}

/**
 * Request body for user login
 */
export interface LoginRequest {
  access_code: string;
}

/**
 * Response from user login
 */
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: number;
  access_code: string;
  platform_registered: PlatformType;
  balance: string; // Decimal serialized as string
  telegram_id?: number[]; // List of linked Telegram IDs
  is_admin: boolean;
}

/**
 * Request body for token refresh
 */
export interface RefreshTokenRequest {
  refresh_token: string;
}

/**
 * Response from token refresh
 */
export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
}

/**
 * Response from token verification
 */
export interface TokenVerifyResponse {
  valid: boolean;
  user_id?: number;
  access_code?: string;
  expires_at?: string;
}

// ============================================================================
// USER TYPES
// ============================================================================

/**
 * User profile information
 * Note: Matches backend schema backend/schemas/user.py:UserProfileResponse
 */
export interface UserProfile {
  user_id: number;
  access_code: string;
  balance: string; // Decimal serialized as string
  datestamp: string;
  platform_registered: PlatformType;
  language: string;
  username?: string;
  telegram_id?: number[]; // List of linked Telegram IDs (includes owner + additional)
  telegram_id_owner?: number; // Telegram ID of the account owner (first element of telegram_id)
  linked_telegram_ids: number[]; // Additional linked Telegram IDs (excluding the owner)
  balance_forward?: number | null; // User ID whose balance is used if set
  referral_link_bot: string;
  referral_link_web: string;
  myreferal_id: string;
  referal_quantity: number;
  total_earned_from_referrals: string; // Decimal serialized as string
}

/**
 * Single user history item
 */
export interface UserHistoryItem {
  id_log: number;
  action_type: string;
  action_description: string;
  date_of_action: string;
  formatted_message: string;
}

/**
 * Response from user history endpoint
 */
export interface UserHistoryResponse {
  history: UserHistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Request body for coupon activation
 */
export interface ActivateCouponRequest {
  coupon_code: string;
}

/**
 * Response from coupon activation
 * Note: Matches backend schema backend/schemas/user.py:ActivateCouponResponse
 */
export interface ActivateCouponResponse {
  success: boolean;
  message: string;
  coupon_code: string;
  discount_percentage: string; // Decimal serialized as string
  discount_amount?: string; // Decimal serialized as string
  expires_at?: string;
  usage_info: string; // Information about coupon usage limits as formatted string
}

/**
 * Single referral item
 */
export interface ReferralItem {
  user_id: number;
  username?: string;
  datestamp: string;
  total_spent: string;
  bonus_earned: string;
  is_active: boolean;
}

/**
 * Response from referrals endpoint
 */
export interface ReferralsResponse {
  referrals: ReferralItem[];
  total_referrals: number;
  total_earned: string;
  referral_bonus_percentage: number;
  page: number;
  page_size: number;
}

// ============================================================================
// PRODUCTS TYPES
// ============================================================================

/**
 * Single proxy product item
 * Note: Matches backend schema backend/schemas/products.py:ProxyItem
 */
export interface ProxyItem {
  product_id: number; // Product ID as integer
  ip: string;
  port?: string | null; // Port as string or null
  login?: string;
  password?: string;
  country: string;
  state?: string;
  city?: string;
  zip?: string;
  ISP?: string;
  ORG?: string;
  speed?: string | null; // Speed as string or null
  price: string; // Decimal serialized as string
  datestamp: string;
}

/**
 * Response from products list endpoint
 * Note: Matches backend schema backend/schemas/products.py:ProductsListResponse
 */
export interface ProductsListResponse {
  products: ProxyItem[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
  filters: Record<string, string | null>; // Flexible filter structure matching backend Dict[str, Optional[str]]
}

/**
 * Country list item with available count
 */
export interface CountryListItem {
  country: string;
  country_code: string;
  flag: string;
  available_count: number;
}

/**
 * State list item with available count
 */
export interface StateListItem {
  state: string;
  available_count: number;
}

// ============================================================================
// PURCHASE TYPES
// ============================================================================

/**
 * Request body for proxy purchase
 * Note: Matches backend schema backend/schemas/purchase.py:PurchaseRequest
 */
export interface PurchaseRequest {
  product_id?: number; // Product ID as integer (required for SOCKS5)
  quantity: number;
  coupon_code?: string;
  country?: string; // Required for PPTP
  state?: string;
  city?: string;
  zip_code?: string;
}

/**
 * Response from proxy purchase
 * Note: Matches backend schema backend/schemas/purchase.py:PurchaseResponse
 */
export interface PurchaseResponse {
  success: boolean;
  order_id?: string;
  product_id: number; // Product ID as integer
  quantity: number;
  price: string; // Decimal serialized as string
  original_price: string; // Decimal serialized as string
  discount_applied?: string; // Decimal serialized as string
  country: string;
  state?: string;
  city?: string;
  zip?: string;
  proxies: Array<Record<string, any>>; // Flexible proxy structure
  expires_at: string;
  hours_left: number;
  new_balance: string; // Decimal serialized as string
}

/**
 * Single purchase history item
 * Note: Matches backend schema backend/schemas/purchase.py:PurchaseHistoryItem
 */
export interface PurchaseHistoryItem {
  id: number;
  order_id?: string;
  proxy_type: ProxyType;
  quantity: number;
  price: string; // Decimal serialized as string
  country: string;
  state?: string;
  city?: string;
  zip?: string;
  proxies: Array<Record<string, any>>; // Flexible proxy structure
  datestamp: string;
  expires_at: string;
  hours_left: number;
  isRefunded: boolean;
  resaled: boolean;
  user_key?: string | null; // User key (0 for invalid PPTP, None for valid)
}

/**
 * Response from purchase history endpoint
 */
export interface PurchaseHistoryResponse {
  purchases: PurchaseHistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Response from proxy validation
 * Note: Matches backend schema backend/schemas/purchase.py:ValidateProxyResponse
 */
export interface ValidateProxyResponse {
  proxy_id: number; // Proxy ID as integer
  online: boolean;
  latency_ms?: number;
  exit_ip?: string;
  minutes_since_purchase: number;
  refund_eligible: boolean;
  refund_window_minutes: number;
  message: string;
}

/**
 * Request body for proxy extension
 */
export interface ExtendProxyRequest {
  hours: number;
}

/**
 * Response from proxy extension
 * Note: Matches backend schema backend/schemas/purchase.py:ExtendProxyResponse
 */
export interface ExtendProxyResponse {
  success: boolean;
  proxy_id: number; // Proxy ID as integer
  price: string; // Decimal serialized as string
  new_expires_at: string;
  hours_added: number;
  new_balance: string; // Decimal serialized as string
  message: string;
}

// ============================================================================
// PAYMENT TYPES
// ============================================================================

/**
 * Request body for payment creation
 * Note: amount_usd is optional and Decimal is serialized as string
 */
export interface CreatePaymentRequest {
  amount_usd?: string; // Decimal serialized as string, optional (defaults to MIN_DEPOSIT_USD if not provided)
}

/**
 * Response from payment creation (Heleket invoice)
 * Note: Decimal fields are serialized as strings
 */
export interface CreatePaymentResponse {
  payment_url: string;
  payment_uuid: string;
  order_id: string;
  expired_at?: string;
  amount_usd: string; // Decimal serialized as string
  min_amount_usd: string; // Decimal serialized as string
}

/**
 * Single transaction history item
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
  confirmation?: number;
  payment_uuid?: string;
  order_id?: string;
  transaction_type?: string;
}

/**
 * Response from transaction history endpoint
 */
export interface TransactionHistoryResponse {
  transactions: TransactionHistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

// ============================================================================
// ERROR TYPES
// ============================================================================

/**
 * Standard API error response
 * Note: Matches backend schema backend/schemas/auth.py:ErrorResponse
 * All API methods may throw AxiosError with response.data conforming to this interface
 */
export interface APIError {
  detail: string | Array<{ loc: string[]; msg: string; type: string }> | unknown; // Human-readable error message or Pydantic validation errors
  error_code?: string; // Optional error code for client-side handling
  status?: number; // HTTP status code
}

