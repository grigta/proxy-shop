import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format } from 'date-fns';
import { ru, enUS } from 'date-fns/locale';

/**
 * Utility for merging Tailwind CSS classes
 * Resolves conflicts between Tailwind classes
 * Used in all shadcn/ui components
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format currency for ru/en locales
 * @param amount - Amount to format (string or number)
 * @param locale - Locale code (ru or en)
 * @returns Formatted currency string with $ symbol
 */
export function formatCurrency(amount: string | number, locale: string = 'ru'): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(num);
}

/**
 * Format date for ru/en locales
 * @param date - Date to format (string or Date object)
 * @param locale - Locale code (ru or en)
 * @param formatStr - date-fns format string
 * @returns Formatted date string
 */
export function formatDate(
  date: string | Date, 
  locale: string = 'ru', 
  formatStr: string = 'dd.MM.yyyy, HH:mm:ss'
): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return format(dateObj, formatStr, { 
    locale: locale === 'ru' ? ru : enUS 
  });
}

/**
 * Format proxy data as string
 * SOCKS5: ip:port:login:password
 * PPTP: ip:login:password:state:city:zip
 * @param proxy - Proxy object with credentials
 * @param type - Proxy type (socks5 or pptp)
 * @returns Formatted proxy string
 */
export function formatProxyString(
  proxy: {
    ip: string;
    port?: string;
    login?: string;
    password?: string;
    state?: string;
    city?: string;
    zip?: string;
  },
  type: 'socks5' | 'pptp'
): string {
  if (type === 'socks5') {
    return `${proxy.ip}:${proxy.port}:${proxy.login}:${proxy.password}`;
  }
  // PPTP format: IP:Login:Pass:State:City:Zip
  return `${proxy.ip}:${proxy.login}:${proxy.password}:${proxy.state || ''}:${proxy.city || ''}:${proxy.zip || ''}`;
}

/**
 * Copy text to clipboard
 * @param text - Text to copy
 * @returns Promise resolving to success boolean
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    console.error('Failed to copy:', err);
    return false;
  }
}

/**
 * Calculate hours left until expiration
 * @param expiresAt - Expiration date (string or Date)
 * @returns Hours remaining (minimum 0)
 */
export function calculateHoursLeft(expiresAt: string | Date): number {
  const now = new Date();
  const expiry = typeof expiresAt === 'string' ? new Date(expiresAt) : expiresAt;
  const diff = expiry.getTime() - now.getTime();
  return Math.max(0, Math.floor(diff / (1000 * 60 * 60)));
}

/**
 * Get color for proxy status based on hours left
 * @param hoursLeft - Hours remaining
 * @param isRefunded - Whether proxy was refunded
 * @returns Color name for styling
 */
export function getStatusColor(
  hoursLeft: number, 
  isRefunded: boolean
): 'green' | 'yellow' | 'red' | 'gray' {
  if (isRefunded) return 'gray';
  if (hoursLeft > 12) return 'green';
  if (hoursLeft > 6) return 'yellow';
  if (hoursLeft > 0) return 'red';
  return 'gray';
}

/**
 * Parse time duration into hours and minutes
 * @param minutes - Total minutes
 * @returns Object with hours and minutes
 */
export function parseMinutesToTime(minutes: number): { hours: number; minutes: number } {
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return { hours, minutes: remainingMinutes };
}

/**
 * Validate access code format (XXX-XXX-XXX)
 * Allowed characters: A-Z (excluding I, O) and 2-9 (excluding 0, 1)
 * @param code - Access code to validate
 * @returns Whether code is valid
 */
export function validateAccessCode(code: string): boolean {
  const pattern = /^[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{3}-[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{3}-[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{3}$/;
  return pattern.test(code);
}

/**
 * Format access code with dashes as user types
 * Filters out invalid characters (I, O, 0, 1)
 * @param value - Input value
 * @returns Formatted access code
 */
export function formatAccessCodeInput(value: string): string {
  // Remove all characters except allowed ones: A-Z (excluding I, O) and 2-9 (excluding 0, 1)
  const cleaned = value.toUpperCase().replace(/[^ABCDEFGHJKLMNPQRSTUVWXYZ23456789]/g, '');

  // Add dashes at positions 3 and 6
  let formatted = '';
  for (let i = 0; i < cleaned.length && i < 9; i++) {
    if (i === 3 || i === 6) {
      formatted += '-';
    }
    formatted += cleaned[i];
  }

  return formatted;
}

/**
 * Get blockchain explorer URL for transaction
 * @param chain - Blockchain name
 * @param txid - Transaction ID
 * @returns Explorer URL
 */
export function getExplorerUrl(chain: string, txid: string): string {
  const explorers: Record<string, string> = {
    bitcoin: `https://blockchair.com/bitcoin/transaction/${txid}`,
    ethereum: `https://etherscan.io/tx/${txid}`,
    bsc: `https://bscscan.com/tx/${txid}`,
    tron: `https://tronscan.org/#/transaction/${txid}`,
    litecoin: `https://blockchair.com/litecoin/transaction/${txid}`
  };
  
  return explorers[chain.toLowerCase()] || '#';
}

