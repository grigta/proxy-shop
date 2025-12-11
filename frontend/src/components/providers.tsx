'use client';

import { ChakraProvider } from '@chakra-ui/react';
import { NextUIProvider } from '@nextui-org/react';
import { ThemeProvider } from 'next-themes';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { NextIntlClientProvider } from 'next-intl';
import { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/auth-store';

/**
 * Providers component that wraps the entire application
 * 
 * Provider order is important:
 * 1. NextIntlClientProvider - i18n for all components
 * 2. QueryClientProvider - React Query for server state management
 * 3. ThemeProvider - Dark mode support via next-themes
 * 4. ChakraProvider - Chakra UI components (Stack, Grid, Container)
 * 5. NextUIProvider - NextUI components (Avatar, Badge, Chip)
 * 6. ReactQueryDevtools - Development tools (only in development)
 */
export function Providers({
  children,
  locale,
  messages
}: {
  children: React.ReactNode;
  locale: string;
  messages: any;
}) {
  // Create QueryClient inside component to avoid shared state between requests
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Data is considered fresh for 1 minute
            staleTime: 60 * 1000,
            // Don't refetch on window focus to avoid unnecessary requests
            refetchOnWindowFocus: false,
            // Retry failed requests once
            retry: 1
          }
        }
      })
  );

  // Initialize auth store from cookies on mount
  useEffect(() => {
    useAuthStore.getState().initialize();
  }, []);

  return (
    <NextIntlClientProvider locale={locale} messages={messages}>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider 
          attribute="class" 
          defaultTheme="dark" 
          enableSystem
        >
          <ChakraProvider>
            <NextUIProvider>
              {children}
              {/* React Query devtools - only visible in development */}
              <ReactQueryDevtools initialIsOpen={false} />
            </NextUIProvider>
          </ChakraProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </NextIntlClientProvider>
  );
}

