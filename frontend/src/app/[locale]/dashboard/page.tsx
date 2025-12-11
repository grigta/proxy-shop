/**
 * Dashboard page
 * Shows user profile, balance, referral info
 */

'use client';

import { useUserProfile } from '@/hooks/use-api';
import { useTranslations, useLocale } from 'next-intl';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Navbar } from '@/components/layout/navbar';
import { formatDate, copyToClipboard } from '@/lib/utils';
import { useToast } from '@/components/ui/use-toast';
import { Copy, ExternalLink, Wallet, History, Users } from 'lucide-react';
import Link from 'next/link';

/**
 * Dashboard page component
 * Main page after login showing user profile
 */
export default function DashboardPage() {
  const { data: profile, isLoading } = useUserProfile();
  const t = useTranslations('account');
  const locale = useLocale();
  const { toast } = useToast();

  const handleCopy = async (text: string, label: string) => {
    const success = await copyToClipboard(text);
    if (success) {
      toast({
        title: 'Скопировано!',
        description: `${label} скопирован в буфер обмена`,
        variant: 'default'
      });
    }
  };

  if (isLoading) {
    return (
      <>
        <Navbar />
        <div className="container mx-auto px-4 py-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Skeleton className="h-64" />
            <Skeleton className="h-64" />
          </div>
        </div>
      </>
    );
  }

  if (!profile) {
    return (
      <>
        <Navbar />
        <div className="container mx-auto px-4 py-8">
          <div className="text-center text-muted-foreground">
            Не удалось загрузить профиль
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Profile Card */}
          <Card>
            <CardHeader>
              <CardTitle>{t('title')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">{t('accId')}:</span>
                <span className="font-medium">{profile.user_id}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">{t('balance')}:</span>
                <Badge variant="default" className="text-lg px-3 py-1">
                  {profile.balance}$
                </Badge>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">{t('regDate')}:</span>
                <span className="font-medium">{formatDate(profile.datestamp)}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">{t('referrals')}:</span>
                <Badge variant="secondary">
                  {profile.referal_quantity}
                </Badge>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Заработано:</span>
                <Badge variant="outline">
                  {profile.total_earned_from_referrals}$
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Referral Card */}
          <Card>
            <CardHeader>
              <CardTitle>Реферальные ссылки</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Bot Link:</p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-xs bg-muted p-2 rounded overflow-x-auto">
                    {profile.referral_link_bot}
                  </code>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleCopy(profile.referral_link_bot, 'Bot link')}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <div>
                <p className="text-sm text-muted-foreground mb-1">Web Link:</p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-xs bg-muted p-2 rounded overflow-x-auto">
                    {profile.referral_link_web}
                  </code>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleCopy(profile.referral_link_web, 'Web link')}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions Card */}
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>{t('quickActions')}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Button asChild className="h-auto py-4">
                  <Link href={`/${locale}/payment`}>
                    <div className="text-center">
                      <Wallet className="h-6 w-6 mx-auto mb-2" />
                      <div className="font-medium">{t('depositBalance')}</div>
                    </div>
                  </Link>
                </Button>

                <Button asChild variant="outline" className="h-auto py-4">
                  <Link href={`/${locale}/history`}>
                    <div className="text-center">
                      <History className="h-6 w-6 mx-auto mb-2" />
                      <div className="font-medium">{t('accountHistory')}</div>
                    </div>
                  </Link>
                </Button>

                <Button asChild variant="outline" className="h-auto py-4">
                  <Link href={`/${locale}/referrals`}>
                    <div className="text-center">
                      <Users className="h-6 w-6 mx-auto mb-2" />
                      <div className="font-medium">{t('myReferrals')}</div>
                    </div>
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}

