/**
 * Purchase History page
 * View and manage purchased proxies with validation and extension
 */

'use client';

import { useState } from 'react';
import { usePurchaseHistory, useValidateProxy, useExtendProxy } from '@/hooks/use-api';
import { useAuthStore } from '@/store/auth-store';
import { useTranslations, useLocale } from 'next-intl';
import { Navbar } from '@/components/layout/navbar';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { formatDate, calculateHoursLeft, formatProxyString, copyToClipboard } from '@/lib/utils';
import { useToast } from '@/components/ui/use-toast';
import { Copy, CheckCircle, Clock } from 'lucide-react';
import Link from 'next/link';
import type { ProxyType } from '@/types/api';

export default function HistoryPage() {
  const { user } = useAuthStore();
  const t = useTranslations('history');
  const locale = useLocale();
  const { toast } = useToast();

  const [proxyTypeFilter, setProxyTypeFilter] = useState<ProxyType | 'ALL'>('ALL');
  const [validateDialogOpen, setValidateDialogOpen] = useState(false);
  const [extendDialogOpen, setExtendDialogOpen] = useState(false);
  const [selectedProxy, setSelectedProxy] = useState<any>(null);
  const [extendHours, setExtendHours] = useState('24');

  const { data: history, isLoading } = usePurchaseHistory(
    user?.user_id || 0,
    { 
      proxy_type: proxyTypeFilter === 'ALL' ? undefined : proxyTypeFilter,
      page: 1, 
      page_size: 50 
    },
    { enabled: !!user }
  );

  const validateMutation = useValidateProxy();
  const extendMutation = useExtendProxy();

  const handleCopy = async (proxy: any, type: string) => {
    const proxyStr = formatProxyString(proxy, type.toLowerCase() as 'socks5' | 'pptp');
    const success = await copyToClipboard(proxyStr);
    if (success) {
      toast({
        title: t('copied'),
        variant: 'default'
      });
    }
  };

  const handleValidateClick = (purchase: any, proxy: any) => {
    setSelectedProxy({ ...proxy, purchase });
    setValidateDialogOpen(true);
  };

  const handleValidate = async () => {
    if (selectedProxy) {
      validateMutation.mutate({
        proxyId: selectedProxy.purchase.id,
        proxyType: selectedProxy.purchase.proxy_type as ProxyType
      });
      setValidateDialogOpen(false);
    }
  };

  const handleExtendClick = (purchase: any, proxy: any) => {
    setSelectedProxy({ ...proxy, purchase });
    setExtendDialogOpen(true);
  };

  const handleExtend = async () => {
    if (selectedProxy && extendHours) {
      extendMutation.mutate({
        proxyId: selectedProxy.purchase.id,
        proxyType: selectedProxy.purchase.proxy_type as ProxyType,
        data: { hours: parseInt(extendHours) }
      });
      setExtendDialogOpen(false);
      setExtendHours('24');
    }
  };

  const calculateExtendPrice = () => {
    if (!selectedProxy || !extendHours) return '0.00';
    // Assuming $5 per 24 hours as base price
    const basePrice = 5;
    const hours = parseInt(extendHours) || 0;
    return ((basePrice / 24) * hours).toFixed(2);
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

  if (!history || history.purchases.length === 0) {
    return (
      <>
        <Navbar />
        <div className="container mx-auto px-4 py-8">
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-muted-foreground mb-6">{t('noPurchases')}</p>
              <div className="flex gap-3 justify-center">
                <Button asChild>
                  <Link href={`/${locale}/socks5`}>{t('goToSocks5')}</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link href={`/${locale}/pptp`}>{t('goToPptp')}</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardHeader>
            <CardTitle>📜 {t('title')}</CardTitle>
          </CardHeader>
          <CardContent>
            {/* Filter Tabs */}
            <Tabs value={proxyTypeFilter} onValueChange={(v) => setProxyTypeFilter(v as any)} className="mb-6">
              <TabsList>
                <TabsTrigger value="ALL">Все</TabsTrigger>
                <TabsTrigger value="SOCKS5">SOCKS5</TabsTrigger>
                <TabsTrigger value="PPTP">PPTP</TabsTrigger>
              </TabsList>
            </Tabs>

            {/* Purchases List */}
            <div className="space-y-4">
              {history.purchases.map((purchase) => {
                const hoursLeft = calculateHoursLeft(purchase.expires_at);
                
                return (
                  <Card key={purchase.id}>
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <Badge variant={purchase.proxy_type === 'SOCKS5' ? 'default' : 'secondary'}>
                            {purchase.proxy_type}
                          </Badge>
                          {purchase.order_id && (
                            <span className="ml-2 text-sm text-muted-foreground">
                              {t('orderId')}: {purchase.order_id}
                            </span>
                          )}
                        </div>
                        <Badge variant={hoursLeft > 12 ? 'default' : hoursLeft > 0 ? 'destructive' : 'outline'}>
                          {hoursLeft}h {t('expires')}
                        </Badge>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm mb-4">
                        <div>
                          <span className="text-muted-foreground">{t('country')}:</span>
                          <span className="ml-2 font-medium">{purchase.country}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">{t('price')}:</span>
                          <span className="ml-2 font-medium">{purchase.price}$</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">{t('date')}:</span>
                          <span className="ml-2 font-medium">{formatDate(purchase.datestamp)}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">{t('status')}:</span>
                          <Badge variant={purchase.isRefunded ? 'outline' : 'default'} className="ml-2">
                            {purchase.isRefunded ? t('refunded') : t('active')}
                          </Badge>
                        </div>
                      </div>

                      {purchase.proxies.length > 0 && (
                        <div className="space-y-2">
                          {purchase.proxies.map((proxy: any, idx: number) => (
                            <div key={idx} className="flex items-center gap-2 bg-muted p-2 rounded">
                              <code className="flex-1 text-xs">
                                {formatProxyString(proxy, purchase.proxy_type.toLowerCase() as 'socks5' | 'pptp')}
                              </code>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleCopy(proxy, purchase.proxy_type)}
                              >
                                <Copy className="h-4 w-4" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      )}

                      <div className="flex gap-2 mt-4">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleValidateClick(purchase, purchase.proxies[0])}
                        >
                          <CheckCircle className="h-4 w-4 mr-2" />
                          {t('validateProxy')}
                        </Button>
                        
                        {!purchase.isRefunded && hoursLeft > 0 && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleExtendClick(purchase, purchase.proxies[0])}
                          >
                            <Clock className="h-4 w-4 mr-2" />
                            {t('extendProxy')}
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Validate Dialog */}
      <Dialog open={validateDialogOpen} onOpenChange={setValidateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('validateProxy')}</DialogTitle>
            <DialogDescription>
              Проверка статуса прокси-сервера
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm text-muted-foreground">
              Вы уверены, что хотите проверить статус этого прокси?
            </p>
            {validateMutation.isSuccess && (
              <div className={`mt-4 p-3 rounded ${validateMutation.data?.online ? 'bg-green-50 dark:bg-green-950/30 text-green-900 dark:text-green-100' : 'bg-red-50 dark:bg-red-950/30 text-red-900 dark:text-red-100'}`}>
                <p className="font-medium">{validateMutation.data?.message}</p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setValidateDialogOpen(false)}>
              {t('cancel')}
            </Button>
            <Button onClick={handleValidate} disabled={validateMutation.isPending}>
              {validateMutation.isPending ? 'Проверка...' : 'Проверить'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Extend Dialog */}
      <Dialog open={extendDialogOpen} onOpenChange={setExtendDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('extendProxy')}</DialogTitle>
            <DialogDescription>
              Продление срока действия прокси
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-4">
            <div>
              <label htmlFor="hours" className="text-sm font-medium mb-2 block">
                {t('hours')}:
              </label>
              <Input
                id="hours"
                type="number"
                min="1"
                max="720"
                value={extendHours}
                onChange={(e) => setExtendHours(e.target.value)}
                placeholder="24"
              />
            </div>
            
            <div className="bg-muted p-3 rounded space-y-1">
              <p className="text-sm">
                {t('extendInfo', { price: calculateExtendPrice() })}
              </p>
              <p className="text-sm">
                {t('currentBalance', { balance: user?.balance })}
              </p>
              <p className="text-sm font-medium">
                {t('newBalance', { 
                  balance: (parseFloat(user?.balance || '0') - parseFloat(calculateExtendPrice())).toFixed(2) 
                })}
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setExtendDialogOpen(false)}>
              {t('cancel')}
            </Button>
            <Button onClick={handleExtend} disabled={extendMutation.isPending || !extendHours}>
              {extendMutation.isPending ? 'Продление...' : t('confirmExtend')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
