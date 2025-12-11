/**
 * Payment page
 * Deposit balance with Heleket universal payment links and view payment history
 */

'use client';

import { useState } from 'react';
import { useGenerateAddress, usePaymentHistory } from '@/hooks/use-api';
import { useAuthStore } from '@/store/auth-store';
import { useTranslations } from 'next-intl';
import { Navbar } from '@/components/layout/navbar';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/components/ui/use-toast';
import { MIN_DEPOSIT_USD } from '@/lib/constants';
import { copyToClipboard, formatDate } from '@/lib/utils';
import { Copy, ExternalLink, RefreshCcw, Wallet } from 'lucide-react';

export default function PaymentPage() {
  const [amount, setAmount] = useState<string>('');
  const { user, refreshUser } = useAuthStore();
  const t = useTranslations('payment');
  const { toast } = useToast();

  const generateMutation = useGenerateAddress();
  const { data: paymentHistory, isLoading: isLoadingHistory } = usePaymentHistory(
    user?.user_id || 0,
    { page: 1, page_size: 20 },
    { enabled: !!user }
  );

  const handleCreatePayment = () => {
    // Validate amount if provided
    if (amount) {
      const parsedAmount = parseFloat(amount);
      
      // Check if the parsed amount is valid
      if (isNaN(parsedAmount)) {
        toast({
          title: t('errorTitle'),
          description: t('invalidAmountError'),
          variant: 'destructive'
        });
        return;
      }
      
      // Check minimum amount
      if (parsedAmount < MIN_DEPOSIT_USD) {
        toast({
          title: t('errorTitle'),
          description: t('minDepositError', { min: MIN_DEPOSIT_USD }),
          variant: 'destructive'
        });
        return;
      }
    }

    // Create payment with optional amount
    generateMutation.mutate({
      amount_usd: amount || undefined
    });
  };

  const handleCopyTxId = async (txid: string) => {
    const success = await copyToClipboard(txid);
    if (success) {
      toast({
        title: t('copied', { defaultValue: 'Скопировано!' }),
        variant: 'default'
      });
    }
  };

  const handleCheckBalance = async () => {
    await refreshUser();
    toast({
      title: t('balanceUpdated'),
      description: t('currentBalance', { balance: user?.balance }),
      variant: 'default'
    });
  };

  const handleCreateNewPayment = () => {
    generateMutation.reset();
    setAmount('');
  };

  const handleOpenPaymentLink = () => {
    if (generateMutation.data?.payment_url) {
      window.open(generateMutation.data.payment_url, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <>
      <Navbar />
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardHeader>
            <CardTitle>💰 {t('title')}</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="deposit" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="deposit">{t('depositTab')}</TabsTrigger>
                <TabsTrigger value="history">{t('paymentHistory')}</TabsTrigger>
              </TabsList>

              {/* Deposit Tab */}
              <TabsContent value="deposit" className="space-y-6">
                {!generateMutation.data ? (
                  <>
                    <div className="bg-muted p-4 rounded-lg space-y-3">
                      <p className="text-sm font-medium">
                        ℹ️ {t('howToDepositTitle')}
                      </p>
                      <ol className="text-sm space-y-2 ml-4 list-decimal">
                        <li>{t('howToDepositStep1')}</li>
                        <li>{t('howToDepositStep2')}</li>
                        <li>{t('howToDepositStep3')}</li>
                        <li>{t('howToDepositStep4')}</li>
                        <li>{t('howToDepositStep5')}</li>
                      </ol>
                    </div>

                    <div className="space-y-4">
                      <div className="space-y-2">
                        <label htmlFor="amount" className="text-sm font-medium">
                          {t('depositAmountLabel')}
                        </label>
                        <Input
                          id="amount"
                          type="number"
                          min={MIN_DEPOSIT_USD}
                          step="0.01"
                          placeholder={t('depositAmountPlaceholder', { min: MIN_DEPOSIT_USD })}
                          value={amount}
                          onChange={(e) => setAmount(e.target.value)}
                          disabled={generateMutation.isLoading}
                        />
                        <p className="text-xs text-muted-foreground">
                          {t('depositAmountHint', { min: MIN_DEPOSIT_USD })}
                        </p>
                      </div>

                      <Button
                        onClick={handleCreatePayment}
                        disabled={generateMutation.isLoading}
                        className="w-full"
                        size="lg"
                      >
                        <Wallet className="h-5 w-5 mr-2" />
                        {generateMutation.isLoading ? t('creatingPayment') : t('depositButton')}
                      </Button>
                    </div>
                  </>
                ) : (
                  <div className="space-y-6">
                    {/* Payment Details Card */}
                    <div className="bg-green-50 dark:bg-green-500/10 p-4 rounded-lg border border-green-200 dark:border-green-500/30 space-y-3">
                      <p className="text-sm font-medium text-green-900 dark:text-green-400 mb-3">
                        ✅ {t('paymentCreatedTitle')}
                      </p>
                      
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">{t('paymentId')}</span>
                          <code className="text-xs">{generateMutation.data.order_id}</code>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">{t('paymentAmount')}</span>
                          <span className="font-medium">{generateMutation.data.amount_usd}$</span>
                        </div>
                        {generateMutation.data.expired_at && (
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">{t('paymentValidUntil')}</span>
                            <span className="text-xs">{formatDate(generateMutation.data.expired_at)}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Payment Link Button */}
                    <Button
                      onClick={handleOpenPaymentLink}
                      className="w-full"
                      size="lg"
                      variant="default"
                    >
                      <ExternalLink className="h-5 w-5 mr-2" />
                      {t('proceedToPayment')}
                    </Button>

                    <div className="bg-muted p-4 rounded-lg">
                      <p className="text-sm text-muted-foreground">
                        ℹ️ {t('paymentAutoCredit')}
                      </p>
                    </div>

                    {/* Check Balance Section */}
                    <div className="bg-blue-50 dark:bg-blue-500/10 p-4 rounded-lg border border-blue-200 dark:border-blue-500/30">
                      <p className="text-sm font-medium text-blue-900 dark:text-blue-400 mb-3">
                        ⏳ {t('awaitingPayment')}
                      </p>
                      <Button
                        variant="default"
                        onClick={handleCheckBalance}
                        className="w-full"
                      >
                        <RefreshCcw className="h-4 w-4 mr-2" />
                        {t('checkBalance')}
                      </Button>
                    </div>

                    {/* Create New Payment */}
                    <div className="flex gap-3">
                      <Button variant="outline" onClick={handleCreateNewPayment} className="w-full">
                        {t('createNewPayment')}
                      </Button>
                    </div>
                  </div>
                )}
              </TabsContent>

              {/* Payment History Tab */}
              <TabsContent value="history">
                {isLoadingHistory ? (
                  <Skeleton className="h-64" />
                ) : paymentHistory && paymentHistory.transactions.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-3 px-4 font-medium text-sm">{t('currency')}</th>
                          <th className="text-right py-3 px-4 font-medium text-sm">{t('amount')}</th>
                          <th className="text-right py-3 px-4 font-medium text-sm">USD</th>
                          <th className="text-left py-3 px-4 font-medium text-sm">{t('txid')}</th>
                          <th className="text-left py-3 px-4 font-medium text-sm">{t('date')}</th>
                          <th className="text-center py-3 px-4 font-medium text-sm">{t('confirmations')}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {paymentHistory.transactions.map((tx) => (
                          <tr key={tx.id_tranz} className="border-b hover:bg-muted/50">
                            <td className="py-3 px-4">
                              <Badge variant="outline">{tx.chain}</Badge>
                            </td>
                            <td className="py-3 px-4 text-right font-medium text-sm">
                              {tx.coin_amount}
                            </td>
                            <td className="py-3 px-4 text-right font-medium text-sm text-green-600">
                              +{tx.amount_in_dollar}$
                            </td>
                            <td className="py-3 px-4">
                              <div className="flex items-center gap-2">
                                <code className="text-xs">
                                  {tx.txid.substring(0, 8)}...{tx.txid.substring(tx.txid.length - 8)}
                                </code>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleCopyTxId(tx.txid)}
                                >
                                  <Copy className="h-3 w-3" />
                                </Button>
                              </div>
                            </td>
                            <td className="py-3 px-4 text-sm text-muted-foreground">
                              {formatDate(tx.dateOfTransaction)}
                            </td>
                            <td className="py-3 px-4 text-center">
                              <Badge variant={tx.confirmation && tx.confirmation >= 1 ? 'default' : 'secondary'}>
                                {tx.confirmation || 0}
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <p className="text-muted-foreground">{t('noPaymentHistory')}</p>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </>
  );
}

