import createMiddleware from 'next-intl/middleware';
import { NextRequest, NextResponse } from 'next/server';
import { locales, defaultLocale } from './i18n';

// Create i18n middleware from next-intl
const intlMiddleware = createMiddleware({
  locales,
  defaultLocale,
  // Don't add /ru prefix in URL for default locale
  localePrefix: 'as-needed'
});

/**
 * Next.js middleware for authentication and i18n
 * 
 * Flow:
 * 1. Check if route requires authentication
 * 2. Verify access_token in cookies
 * 3. Redirect to /login if unauthorized on protected routes
 * 4. Redirect to /dashboard if authorized on public routes
 * 5. Apply i18n middleware for locale handling
 */
export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Protected routes require authentication
  const protectedRoutes = [
    '/dashboard',
    '/socks5',
    '/pptp',
    '/history',
    '/payment',
    '/referrals'
  ];
  
  // Public routes (accessible without authentication)
  const publicRoutes = ['/login', '/register', '/'];
  
  // Get access_token from cookies
  const accessToken = request.cookies.get('access_token')?.value;
  
  // Extract locale from pathname (e.g., /en/dashboard -> en)
  const pathnameLocale = locales.find(
    (locale) => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
  );
  
  // Get the path without locale prefix
  const pathnameWithoutLocale = pathnameLocale
    ? pathname.slice(`/${pathnameLocale}`.length) || '/'
    : pathname;
  
  // Check if current route is protected (using startsWith for exact match)
  const isProtectedRoute = protectedRoutes.some(route => 
    pathnameWithoutLocale.startsWith(route)
  );
  
  // Check if current route is public
  const isPublicRoute = publicRoutes.some(route =>
    pathnameWithoutLocale === route || pathnameWithoutLocale.startsWith('/login') || pathnameWithoutLocale.startsWith('/register')
  );
  
  // Determine the locale to use for redirects
  const locale = pathnameLocale || defaultLocale;
  
  // Redirect to login if accessing protected route without token
  if (isProtectedRoute && !accessToken) {
    // Preserve locale in redirect URL
    const loginUrl = new URL(
      locale !== defaultLocale ? `/${locale}/login` : '/login',
      request.url
    );
    return NextResponse.redirect(loginUrl);
  }
  
  // Redirect to dashboard if accessing public route with valid token
  if (isPublicRoute && accessToken && !pathnameWithoutLocale.startsWith('/login') && !pathnameWithoutLocale.startsWith('/register')) {
    // Preserve locale in redirect URL
    const dashboardUrl = new URL(
      locale !== defaultLocale ? `/${locale}/dashboard` : '/dashboard',
      request.url
    );
    return NextResponse.redirect(dashboardUrl);
  }
  
  // Apply i18n middleware
  return intlMiddleware(request);
}

/**
 * Middleware configuration
 * 
 * Matcher applies middleware to all routes except:
 * - /api routes (API endpoints)
 * - /_next (Next.js internals)
 * - /_vercel (Vercel internals)
 * - Static files with extensions
 */
export const config = {
  matcher: ['/((?!api|_next|_vercel|.*\\..*).*)']
};

