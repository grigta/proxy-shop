/**
 * Application constants
 * Includes API configuration, pagination defaults, pricing, and country data
 */

// ============================================
// API Configuration
// ============================================

// Use relative URLs - Nginx proxies /api/* to backend
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';
export const APP_BASE_URL = process.env.NEXT_PUBLIC_APP_URL || '';

// ============================================
// Pagination
// ============================================

export const DEFAULT_PAGE_SIZE = 10; // For proxy catalog
export const HISTORY_PAGE_SIZE = 20; // For purchase history
export const REFERRALS_PAGE_SIZE = 20; // For referrals list

// ============================================
// Prices (fallback values)
// ============================================

export const SOCKS5_PRICE = 2.0; // Price in USD
export const PPTP_PRICE = 5.0; // Price in USD
export const MIN_DEPOSIT_USD = 10.0; // Minimum deposit

// ============================================
// Refund Windows
// ============================================

export const SOCKS5_REFUND_MINUTES = 30; // Refund window for SOCKS5
export const PPTP_REFUND_HOURS = 24; // Refund window for PPTP

// ============================================
// Durations
// ============================================

export const SOCKS5_DURATION_HOURS = 24; // Duration for SOCKS5
export const PPTP_DURATION_HOURS = 24; // Duration for PPTP

// ============================================
// Crypto Chains
// ============================================

// DEPRECATED: Crypto chain selection removed in favor of Heleket universal payment links (Mode B)
// This array is no longer used in the payment flow but kept for reference
// export const CRYPTO_CHAINS = [
//   { value: 'BTC', label: 'Bitcoin', icon: '₿', network: 'BTC' },
//   { value: 'ETH', label: 'Ethereum', icon: 'Ξ', network: 'Ethereum' },
//   { value: 'LTC', label: 'Litecoin', icon: 'Ł', network: 'Litecoin' },
//   { value: 'BNB', label: 'Binance Coin', icon: '🔶', network: 'BSC' },
//   { value: 'USDT_TRC20', label: 'USDT (TRC-20)', icon: '💵', network: 'Tron' },
//   { value: 'USDT_ERC20', label: 'USDT (ERC-20)', icon: '💵', network: 'Ethereum' },
//   { value: 'USDT_BEP20', label: 'USDT (BEP-20)', icon: '💵', network: 'BSC' }
// ] as const;

// ============================================
// Countries (4 pages from architecture_bot.md)
// ============================================

export const COUNTRIES_PAGES = [
  // Page 1 (15 countries)
  [
    { name: 'United States', code: 'US', flag: '🇺🇸' },
    { name: 'United Kingdom', code: 'GB', flag: '🇬🇧' },
    { name: 'Canada', code: 'CA', flag: '🇨🇦' },
    { name: 'Germany', code: 'DE', flag: '🇩🇪' },
    { name: 'France', code: 'FR', flag: '🇫🇷' },
    { name: 'Netherlands', code: 'NL', flag: '🇳🇱' },
    { name: 'Australia', code: 'AU', flag: '🇦🇺' },
    { name: 'Japan', code: 'JP', flag: '🇯🇵' },
    { name: 'South Korea', code: 'KR', flag: '🇰🇷' },
    { name: 'Switzerland', code: 'CH', flag: '🇨🇭' },
    { name: 'Singapore', code: 'SG', flag: '🇸🇬' },
    { name: 'Ireland', code: 'IE', flag: '🇮🇪' },
    { name: 'Sweden', code: 'SE', flag: '🇸🇪' },
    { name: 'Denmark', code: 'DK', flag: '🇩🇰' },
    { name: 'Norway', code: 'NO', flag: '🇳🇴' }
  ],
  // Page 2 (15 countries)
  [
    { name: 'Italy', code: 'IT', flag: '🇮🇹' },
    { name: 'Spain', code: 'ES', flag: '🇪🇸' },
    { name: 'Portugal', code: 'PT', flag: '🇵🇹' },
    { name: 'Belgium', code: 'BE', flag: '🇧🇪' },
    { name: 'Austria', code: 'AT', flag: '🇦🇹' },
    { name: 'Czech Republic', code: 'CZ', flag: '🇨🇿' },
    { name: 'Poland', code: 'PL', flag: '🇵🇱' },
    { name: 'Greece', code: 'GR', flag: '🇬🇷' },
    { name: 'Hungary', code: 'HU', flag: '🇭🇺' },
    { name: 'Finland', code: 'FI', flag: '🇫🇮' },
    { name: 'Lithuania', code: 'LT', flag: '🇱🇹' },
    { name: 'Latvia', code: 'LV', flag: '🇱🇻' },
    { name: 'Estonia', code: 'EE', flag: '🇪🇪' },
    { name: 'Israel', code: 'IL', flag: '🇮🇱' },
    { name: 'United Arab Emirates', code: 'AE', flag: '🇦🇪' }
  ],
  // Page 3 (15 countries)
  [
    { name: 'Mexico', code: 'MX', flag: '🇲🇽' },
    { name: 'Brazil', code: 'BR', flag: '🇧🇷' },
    { name: 'Argentina', code: 'AR', flag: '🇦🇷' },
    { name: 'Chile', code: 'CL', flag: '🇨🇱' },
    { name: 'Colombia', code: 'CO', flag: '🇨🇴' },
    { name: 'Peru', code: 'PE', flag: '🇵🇪' },
    { name: 'India', code: 'IN', flag: '🇮🇳' },
    { name: 'Indonesia', code: 'ID', flag: '🇮🇩' },
    { name: 'Malaysia', code: 'MY', flag: '🇲🇾' },
    { name: 'Thailand', code: 'TH', flag: '🇹🇭' },
    { name: 'Vietnam', code: 'VN', flag: '🇻🇳' },
    { name: 'Philippines', code: 'PH', flag: '🇵🇭' },
    { name: 'South Africa', code: 'ZA', flag: '🇿🇦' },
    { name: 'Turkey', code: 'TR', flag: '🇹🇷' },
    { name: 'Saudi Arabia', code: 'SA', flag: '🇸🇦' }
  ],
  // Page 4 (5 countries)
  [
    { name: 'Kuwait', code: 'KW', flag: '🇰🇼' },
    { name: 'Qatar', code: 'QA', flag: '🇶🇦' },
    { name: 'New Zealand', code: 'NZ', flag: '🇳🇿' },
    { name: 'Hong Kong', code: 'HK', flag: '🇭🇰' },
    { name: 'Taiwan', code: 'TW', flag: '🇹🇼' }
  ]
];

// Flat list of all countries
export const ALL_COUNTRIES = COUNTRIES_PAGES.flat();

// ============================================
// Query Keys for React Query
// ============================================

export const QUERY_KEYS = {
  user: {
    profile: ['user', 'profile'] as const,
    history: (params: any) => ['user', 'history', params] as const,
    referrals: (userId: number, params: any) => ['user', 'referrals', userId, params] as const
  },
  products: {
    socks5: (params: any) => ['products', 'socks5', params] as const,
    pptp: (params: any) => ['products', 'pptp', params] as const,
    countries: (type: string) => ['products', 'countries', type] as const,
    states: (country: string, type: string) => ['products', 'states', country, type] as const
  },
  purchase: {
    history: (userId: number, params: any) => ['purchase', 'history', userId, params] as const
  },
  payment: {
    history: (userId: number, params: any) => ['payment', 'history', userId, params] as const
  }
} as const;

// ============================================
// Routes
// ============================================

export const ROUTES = {
  home: '/',
  login: '/login',
  dashboard: '/dashboard',
  socks5: '/socks5',
  pptp: '/pptp',
  history: '/history',
  payment: '/payment',
  referrals: '/referrals'
} as const;

// ============================================
// External Links
// ============================================

export const TELEGRAM_NEWS_CHANNEL = 'https://t.me/proxyshopchannel';
export const TELEGRAM_MIRROR_CHANNEL = 'https://t.me/proxyshopmir';
export const SUPPORT_TELEGRAM_ID = '8171638354';
export const RULES_TELEGRAPH_URL = 'https://telegra.ph/proxy-shop-rules';

// ============================================
// Types for Constants
// ============================================

// DEPRECATED: Use Heleket universal payment links instead
// export type CryptoChainType = typeof CRYPTO_CHAINS[number]['value'];
export type RouteKey = keyof typeof ROUTES;
export type Country = typeof ALL_COUNTRIES[number];

