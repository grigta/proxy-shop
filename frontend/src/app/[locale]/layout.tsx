import { Inter } from 'next/font/google';
import { Providers } from '@/components/providers';
import { Toaster } from '@/components/ui/toaster';
import { notFound } from 'next/navigation';

// Configure Inter font with Latin and Cyrillic subsets for ru/en support
const inter = Inter({ 
  subsets: ['latin', 'cyrillic'], 
  variable: '--font-inter' 
});

// Supported locales
const locales = ['ru', 'en'];

/**
 * Locale layout component
 * - Wraps all pages with necessary providers (Chakra, NextUI, React Query, Zustand, next-themes, next-intl)
 * - Provides toast notifications via shadcn/ui Toaster
 * - Handles dark mode via suppressHydrationWarning
 * - Receives locale parameter from next-intl routing
 */
export default async function LocaleLayout({
  children,
  params: { locale }
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  // Validate locale
  if (!locales.includes(locale)) {
    notFound();
  }

  // Load messages for the locale
  let messages;
  try {
    messages = (await import(`../../../messages/${locale}.json`)).default;
  } catch (error) {
    notFound();
  }

  return (
    <html lang={locale} suppressHydrationWarning>
      <body className={inter.className}>
        <Providers locale={locale} messages={messages}>
          {children}
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}

