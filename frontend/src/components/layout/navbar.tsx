/**
 * Navbar component
 * Main navigation bar with links and user menu
 */

'use client';

import { useAuthStore } from '@/store/auth-store';
import { useTranslations, useLocale } from 'next-intl';
import { usePathname, useRouter } from 'next/navigation';
import { useTheme } from 'next-themes';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import Link from 'next/link';
import { Home, ShoppingBag, History, Wallet, Users, LogOut, Moon, Sun, Globe } from 'lucide-react';
import { useState, useEffect } from 'react';

/**
 * Navbar component with navigation links
 * Shows balance and user actions
 */
export function Navbar() {
  const { user, logout } = useAuthStore();
  const t = useTranslations('nav');
  const pathname = usePathname();
  const router = useRouter();
  const locale = useLocale();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Prevent hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!user) return null;

  const isActive = (path: string) => pathname?.includes(path);

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  const toggleLocale = () => {
    const newLocale = locale === 'ru' ? 'en' : 'ru';
    // Get current path without locale prefix
    const pathWithoutLocale = pathname.replace(/^\/(ru|en)/, '') || '/';
    // Navigate to new locale
    router.push(`/${newLocale}${pathWithoutLocale}`);
  };

  return (
    <nav className="sticky top-0 z-50 border-b shadow-sm bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href={`/${locale}/dashboard`} className="font-bold text-xl">
            Proxy Shop
          </Link>

          {/* Navigation Links - Desktop */}
          <div className="hidden md:flex items-center gap-1">
            <Button
              variant={isActive('/dashboard') ? 'default' : 'ghost'}
              size="sm"
              asChild
            >
              <Link href={`/${locale}/dashboard`}>
                <Home className="h-4 w-4 mr-2" />
                {t('dashboard')}
              </Link>
            </Button>

            <Button
              variant={isActive('/socks5') ? 'default' : 'ghost'}
              size="sm"
              asChild
            >
              <Link href={`/${locale}/socks5`}>
                <ShoppingBag className="h-4 w-4 mr-2" />
                {t('socks5')}
              </Link>
            </Button>

            <Button
              variant={isActive('/pptp') ? 'default' : 'ghost'}
              size="sm"
              asChild
            >
              <Link href={`/${locale}/pptp`}>
                <ShoppingBag className="h-4 w-4 mr-2" />
                {t('pptp')}
              </Link>
            </Button>

            <Button
              variant={isActive('/history') ? 'default' : 'ghost'}
              size="sm"
              asChild
            >
              <Link href={`/${locale}/history`}>
                <History className="h-4 w-4 mr-2" />
                {t('history')}
              </Link>
            </Button>

            <Button
              variant={isActive('/payment') ? 'default' : 'ghost'}
              size="sm"
              asChild
            >
              <Link href={`/${locale}/payment`}>
                <Wallet className="h-4 w-4 mr-2" />
                {t('payment')}
              </Link>
            </Button>

            <Button
              variant={isActive('/referrals') ? 'default' : 'ghost'}
              size="sm"
              asChild
            >
              <Link href={`/${locale}/referrals`}>
                <Users className="h-4 w-4 mr-2" />
                {t('referrals')}
              </Link>
            </Button>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3">
            <Badge variant="default" className="text-sm px-3 py-1">
              💰 {user.balance}$
            </Badge>

            {/* Language Toggle */}
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={toggleLocale}
              title={locale === 'ru' ? 'Switch to English' : 'Переключить на русский'}
            >
              <Globe className="h-4 w-4 mr-1" />
              {locale.toUpperCase()}
            </Button>

            {/* Theme Toggle */}
            {mounted && (
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={toggleTheme}
                title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              >
                {theme === 'dark' ? (
                  <Sun className="h-4 w-4" />
                ) : (
                  <Moon className="h-4 w-4" />
                )}
              </Button>
            )}

            <Button variant="ghost" size="sm" onClick={logout}>
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
}

