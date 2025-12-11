import { getRequestConfig } from 'next-intl/server';
import { notFound } from 'next/navigation';

/**
 * Supported locales for the application
 * - ru: Russian (default)
 * - en: English
 */
export const locales = ['ru', 'en'] as const;
export type Locale = typeof locales[number];

// Default locale is Russian
export const defaultLocale: Locale = 'ru';

/**
 * next-intl configuration
 * 
 * This function is called on every request to:
 * 1. Validate the requested locale
 * 2. Load the appropriate translation messages
 * 
 * Translation files are located in:
 * - /messages/ru.json
 * - /messages/en.json
 */
export default getRequestConfig(async ({ locale }) => {
  // Validate that the incoming locale parameter is valid
  if (!locales.includes(locale as any)) {
    notFound();
  }

  return {
    messages: (await import(`../messages/${locale}.json`)).default
  };
});

