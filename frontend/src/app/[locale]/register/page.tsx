/**
 * Registration page
 * Allows users to create new account
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { useTranslations } from 'next-intl';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, Copy, Check } from 'lucide-react';
import { PlatformType } from '@/types/api';
import Link from 'next/link';

/**
 * Registration page component
 * User provides language and optional referral code
 */
export default function RegisterPage() {
  const [language, setLanguage] = useState<string>('ru');
  const [referralCode, setReferralCode] = useState('');
  const [error, setError] = useState('');
  const [registeredAccessCode, setRegisteredAccessCode] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const { register, isLoading } = useAuthStore();
  const router = useRouter();
  const t = useTranslations('auth');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      const result = await register({
        platform: PlatformType.WEB,
        language,
        referral_code: referralCode || undefined
      });

      // Show generated access code
      setRegisteredAccessCode(result.accessCode);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('registrationFailed'));
    }
  };

  const handleCopyCode = async () => {
    if (registeredAccessCode) {
      await navigator.clipboard.writeText(registeredAccessCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleContinueToDashboard = () => {
    router.push('/dashboard');
  };

  // Show success screen with access code
  if (registeredAccessCode) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-background to-muted p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold text-green-600">
              {t('registrationSuccess')}
            </CardTitle>
            <p className="text-muted-foreground mt-2">{t('saveAccessCode')}</p>
          </CardHeader>

          <CardContent className="space-y-6">
            <div className="bg-muted p-6 rounded-lg text-center">
              <p className="text-sm text-muted-foreground mb-2">
                {t('yourAccessCode')}
              </p>
              <div className="text-4xl font-bold tracking-wider mb-4 font-mono">
                {registeredAccessCode}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopyCode}
                className="w-full"
              >
                {copied ? (
                  <>
                    <Check className="mr-2 h-4 w-4" />
                    {t('copied')}
                  </>
                ) : (
                  <>
                    <Copy className="mr-2 h-4 w-4" />
                    {t('copyCode')}
                  </>
                )}
              </Button>
            </div>

            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-4 rounded-lg">
              <p className="text-sm text-yellow-800 dark:text-yellow-200">
                {t('accessCodeWarning')}
              </p>
            </div>
          </CardContent>

          <CardFooter>
            <Button
              onClick={handleContinueToDashboard}
              className="w-full"
            >
              {t('continueToDashboard')}
            </Button>
          </CardFooter>
        </Card>
      </div>
    );
  }

  // Show registration form
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-background to-muted p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-3xl font-bold">Proxy Shop</CardTitle>
          <p className="text-muted-foreground mt-2">{t('register')}</p>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div>
              <label htmlFor="language" className="block text-sm font-medium mb-2">
                {t('language')}
              </label>
              <Select value={language} onValueChange={setLanguage} disabled={isLoading}>
                <SelectTrigger id="language">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ru">Русский</SelectItem>
                  <SelectItem value="en">English</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label htmlFor="referralCode" className="block text-sm font-medium mb-2">
                {t('referralCode')}
              </label>
              <Input
                id="referralCode"
                type="text"
                placeholder={t('referralCodePlaceholder')}
                value={referralCode}
                onChange={(e) => setReferralCode(e.target.value)}
                disabled={isLoading}
              />
              <p className="text-xs text-muted-foreground mt-1">
                {t('referralCodeOptional')}
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
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t('loading')}
                </>
              ) : (
                t('registerButton')
              )}
            </Button>

            <p className="text-sm text-center text-muted-foreground">
              {t('alreadyHaveAccount')}{' '}
              <Link href="/login" className="text-primary hover:underline font-medium">
                {t('loginHere')}
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
