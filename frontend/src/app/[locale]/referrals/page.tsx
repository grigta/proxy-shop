/**
 * Referrals page
 * View referral statistics and referral list
 */

'use client';

import { useReferrals } from '@/hooks/use-api';
import { useAuthStore } from '@/store/auth-store';
import { Navbar } from '@/components/layout/navbar';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import { useTranslations } from 'next-intl';
import { formatDate, copyToClipboard } from '@/lib/utils';
import { Copy, Share2, CheckCircle } from 'lucide-react';

export default function ReferralsPage() {
  const { user } = useAuthStore();
  const t = useTranslations('referrals');
  const { toast } = useToast();

  const { data: referrals, isLoading } = useReferrals(
    user?.user_id || 0,
    { page: 1, page_size: 50 },
    { enabled: !!user }
  );

  const handleCopy = async (text: string, label: string) => {
    const success = await copyToClipboard(text);
    if (success) {
      toast({
        title: t('copied', { defaultValue: 'Скопировано!' }),
        description: `${label} ${t('copied')}`,
        variant: 'default'
      });
    }
  };

  const handleShare = async (text: string, label: string) => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Proxy Shop',
          text: `${label}: ${text}`
        });
      } catch (err) {
        console.log('Share cancelled', err);
      }
    } else {
      // Fallback to copy
      handleCopy(text, label);
    }
  };

  if (isLoading) {
    return (
      <>
        <Navbar />
        <div className="container mx-auto px-4 py-8">
          <Skeleton className="h-96" />
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="container mx-auto px-4 py-8 space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6 text-center">
              <div className="text-3xl font-bold">{referrals?.total_referrals || 0}</div>
              <div className="text-sm text-muted-foreground">{t('totalReferrals')}</div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6 text-center">
              <div className="text-3xl font-bold">{referrals?.total_earned || '0.00'}$</div>
              <div className="text-sm text-muted-foreground">{t('totalEarned')}</div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6 text-center">
              <div className="text-3xl font-bold">{referrals?.referral_bonus_percentage || 0}%</div>
              <div className="text-sm text-muted-foreground">{t('bonusPercentage')}</div>
            </CardContent>
          </Card>
        </div>

        {/* Referral Links Card */}
        <Card>
          <CardHeader>
            <CardTitle>{t('yourLinks')}</CardTitle>
            <p className="text-sm text-muted-foreground">
              {t('shareInfo', { percentage: referrals?.referral_bonus_percentage || 0 })}
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Bot Link */}
            <div>
              <p className="text-sm font-medium mb-2">{t('botLink')}:</p>
              <div className="flex items-center gap-2">
                <code className="flex-1 text-xs bg-muted p-3 rounded overflow-x-auto">
                  {user?.referral_link_bot}
                </code>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleCopy(user?.referral_link_bot || '', t('botLink'))}
                >
                  <Copy className="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleShare(user?.referral_link_bot || '', t('botLink'))}
                >
                  <Share2 className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Web Link */}
            <div>
              <p className="text-sm font-medium mb-2">{t('webLink')}:</p>
              <div className="flex items-center gap-2">
                <code className="flex-1 text-xs bg-muted p-3 rounded overflow-x-auto">
                  {user?.referral_link_web}
                </code>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleCopy(user?.referral_link_web || '', t('webLink'))}
                >
                  <Copy className="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleShare(user?.referral_link_web || '', t('webLink'))}
                >
                  <Share2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Referrals Table Card */}
        <Card>
          <CardHeader>
            <CardTitle>{t('title')}</CardTitle>
          </CardHeader>
          <CardContent>
            {referrals && referrals.referrals.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-4 font-medium text-sm">{t('username')}</th>
                      <th className="text-left py-3 px-4 font-medium text-sm">{t('registrationDate')}</th>
                      <th className="text-right py-3 px-4 font-medium text-sm">{t('totalSpent')}</th>
                      <th className="text-right py-3 px-4 font-medium text-sm">{t('bonusEarned')}</th>
                      <th className="text-center py-3 px-4 font-medium text-sm">{t('status')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {referrals.referrals.map((referral) => (
                      <tr key={referral.user_id} className="border-b hover:bg-muted/50">
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-medium">
                              {referral.username ? referral.username[0].toUpperCase() : '?'}
                            </div>
                            <span className="text-sm">
                              {referral.username || `User ${referral.user_id}`}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-sm text-muted-foreground">
                          {formatDate(referral.datestamp)}
                        </td>
                        <td className="py-3 px-4 text-right font-medium text-sm">
                          {referral.total_spent}$
                        </td>
                        <td className="py-3 px-4 text-right font-medium text-sm text-success">
                          +{referral.bonus_earned}$
                        </td>
                        <td className="py-3 px-4 text-center">
                          <Badge variant={referral.is_active ? 'default' : 'outline'}>
                            {referral.is_active ? (
                              <>
                                <CheckCircle className="h-3 w-3 mr-1" />
                                {t('isActive')}
                              </>
                            ) : (
                              t('inactive')
                            )}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-muted-foreground mb-4">{t('noReferrals')}</p>
                <p className="text-sm text-muted-foreground">{t('shareToEarn')}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}

