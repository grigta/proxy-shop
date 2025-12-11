import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Proxy Shop',
  description: 'Buy SOCKS5 and PPTP proxies with cryptocurrency',
  icons: {
    icon: '/favicon.ico'
  }
};

/**
 * Root layout component for the entire application
 * This is a minimal root layout that doesn't have access to locale
 * The actual providers and locale handling are in [locale]/layout.tsx
 */
export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return children;
}

