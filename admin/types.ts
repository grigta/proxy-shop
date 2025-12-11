export type Language = 'en' | 'ru';
export type Theme = 'light' | 'dark';
export type View = 'dashboard' | 'users' | 'coupons' | 'proxies' | 'broadcast';
export type PlatformType = 'telegram' | 'web';

// ============================================================================
// DASHBOARD TYPES (matching backend/schemas/admin.py)
// ============================================================================

export interface PeriodStats {
  revenue: string | number;
  purchases: number;
  deposits: string | number;
  new_users: number;
  refunds: number;
  refunds_amount: string | number;
}

export interface DashboardStatsResponse {
  total_users: number;
  total_revenue: string | number;
  total_purchases: number;
  total_deposits: string | number;
  active_proxies: number;
  refunded_count: number;
  period_stats: {
    '1d': PeriodStats;
    '7d': PeriodStats;
    '30d': PeriodStats;
    'all_time': PeriodStats;
  };
}

export interface RevenueChartData {
  date: string;
  revenue: string | number;
  purchases: number;
  deposits: string | number;
  socks5_count: number;
  pptp_count: number;
}

// ============================================================================
// USER MANAGEMENT TYPES
// ============================================================================

export interface AdminUserListItem {
  user_id: number;
  access_code: string;
  balance: string | number;
  datestamp: string;
  platform_registered: PlatformType;
  language: string;
  username?: string | null;
  telegram_id?: number | null;
  telegram_id_list?: number[] | null;
  total_spent: string | number;
  total_deposited: string | number;
  purchases_count: number;
  last_activity?: string | null;
  is_blocked: boolean;
  blocked_at?: string | null;
  referrals_count: number;
}

export interface AdminUserListResponse {
  users: AdminUserListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface UpdateUserRequest {
  balance?: number;
  is_blocked?: boolean;
  blocked_reason?: string;
  language?: string;
}

export interface UserFilters {
  search?: string;
  platform?: PlatformType;
  date_from?: string;
  date_to?: string;
  min_balance?: number;
  max_balance?: number;
  is_blocked?: boolean;
  page?: number;
  page_size?: number;
}

// ============================================================================
// COUPON TYPES
// ============================================================================

export interface AdminCouponListItem {
  id: number;
  code: string;
  discount_percent: string | number;
  max_uses: number;
  used_count: number;
  is_active: boolean;
  created_at: string;
  expires_at?: string | null;
}

export interface AdminCouponListResponse {
  coupons: AdminCouponListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface CreateCouponRequest {
  code: string;
  discount_percent: number;
  max_uses: number;
  expires_at?: string;
  is_active?: boolean;
}

export interface UpdateCouponRequest {
  discount_percent?: number;
  max_uses?: number;
  is_active?: boolean;
  expires_at?: string;
}

export interface CouponFilters {
  search?: string;
  is_active?: boolean;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

// ============================================================================
// PROXY INVENTORY TYPES
// ============================================================================

export interface ProxyInventoryItem {
  id: number;
  ip: string;
  port: number;
  country: string;
  state?: string | null;
  city?: string | null;
  is_available: boolean;
  price_per_hour: string | number;
  created_at: string;
  notes?: string | null;
}

export interface AdminProxyListResponse {
  proxies: ProxyInventoryItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface CreateProxyRequest {
  ip: string;
  port: number;
  country: string;
  state?: string;
  city?: string;
  price_per_hour: number;
  notes?: string;
}

export interface UpdateProxyAvailabilityRequest {
  is_available: boolean;
  price_per_hour?: number;
  notes?: string;
}

export interface ProxyInventoryFilters {
  country?: string;
  state?: string;
  city?: string;
  is_available?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

// ============================================================================
// LEGACY TYPES (for backwards compatibility)
// ============================================================================

export interface User {
  id: number;
  accessCode: string;
  username: string;
  platform: 'telegram' | 'web';
  balance: number;
  spent: number;
  purchases: number;
  registrationDate: string;
  status: 'active' | 'blocked';
}

export interface Coupon {
  id: number;
  code: string;
  discount: number;
  used: number;
  maxUses: number;
  expiry: string;
  status: 'active' | 'expired';
}

export interface ProxyItem {
  id: number;
  ip: string;
  port: number;
  country: string;
  region: string;
  price: number;
  status: 'available' | 'sold' | 'expired';
  type: 'SOCKS5' | 'HTTP' | 'PPTP';
  addedAt: string;
}

export interface StatCardData {
  title: string;
  value: string | number;
  subtext: string;
  icon: any;
}