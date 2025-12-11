/**
 * Login page
 * Allows users to login with access code
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { useTranslations } from 'next-intl';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2 } from 'lucide-react';
import { formatAccessCodeInput } from '@/lib/utils';
import Link from 'next/link';

/**
 * Login page component
 * User enters access code in XXX-XXX-XXX format
 */
export default function LoginPage() {
  const [accessCode, setAccessCode] = useState('');
  const [error, setError] = useState('');
  const { login, isLoading } = useAuthStore();
  const router = useRouter();
  const t = useTranslations('auth');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await login(accessCode);
      router.push('/dashboard');
    } catch (err: any) {
      setError(t('invalidAccessCode'));
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatAccessCodeInput(e.target.value);
    setAccessCode(formatted);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-background to-muted p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-3xl font-bold">Proxy Shop</CardTitle>
          <p className="text-muted-foreground mt-2">{t('login')}</p>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div>
              <label htmlFor="accessCode" className="block text-sm font-medium mb-2">
                {t('accessCode')}
              </label>
              <Input
                id="accessCode"
                type="text"
                placeholder={t('accessCodePlaceholder')}
                value={accessCode}
                onChange={handleInputChange}
                maxLength={11}
                className="text-center text-lg tracking-wider"
                disabled={isLoading}
                autoFocus
              />
              <p className="text-xs text-muted-foreground mt-1 text-center">
                {t('allowedCharacters') || 'A-Z (кроме I, O) и 2-9 (кроме 0, 1)'}
              </p>
            </div>

            {error && (
              <div className="text-destructive text-sm text-center bg-destructive/10 p-2 rounded">
                {error}
              </div>
            )}
          </CardContent>

          <CardFooter className="flex flex-col space-y-2">
            <Button
              type="submit"
              className="w-full"
              disabled={isLoading || accessCode.length !== 11}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t('loading')}
                </>
              ) : (
                t('loginButton')
              )}
            </Button>

            <p className="text-sm text-center text-muted-foreground">
              {t('noAccount')}{' '}
              <Link href="/register" className="text-primary hover:underline font-medium">
                {t('registerHere')}
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}

