/**
 * PPTP Catalog page
 * Browse and purchase PPTP proxies by region and state
 */

'use client';

import { useState } from 'react';
import { usePptpProducts, useStates, usePurchasePptp } from '@/hooks/use-api';
import { useTranslations } from 'next-intl';
import { Navbar } from '@/components/layout/navbar';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';

export default function PptpPage() {
  const t = useTranslations('pptp');

  const [selectedRegion, setSelectedRegion] = useState<'US' | 'EU' | null>(null);
  const [selectedState, setSelectedState] = useState<string | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<any>(null);
  const [purchaseDialogOpen, setPurchaseDialogOpen] = useState(false);
  const [couponCode, setCouponCode] = useState('');

  const { data: states, isLoading: isLoadingStates } = useStates(
    selectedRegion || '',
    'PPTP',
    { enabled: !!selectedRegion }
  );

  const { data: products, isLoading: isLoadingProducts } = usePptpProducts(
    {
      country: selectedRegion || '',
      state: selectedState || undefined,
      page: 1,
      page_size: 20
    },
    {
      enabled: !!selectedRegion && !!selectedState
    }
  );

  const purchaseMutation = usePurchasePptp();

  const handleRegionSelect = (region: 'US' | 'EU') => {
    setSelectedRegion(region);
    setSelectedState(null);
    setSelectedProduct(null);
  };

  const handleStateSelect = (state: string) => {
    setSelectedState(state);
  };

  const handleBuyClick = (product: any) => {
    setSelectedProduct(product);
    setPurchaseDialogOpen(true);
  };

  const handlePurchaseConfirm = () => {
    if (selectedProduct) {
      purchaseMutation.mutate({
        product_id: selectedProduct.product_id,
        coupon_code: couponCode || undefined
      });
      setPurchaseDialogOpen(false);
      setCouponCode('');
    }
  };

  return (
    <>
      <Navbar />
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardHeader>
            <CardTitle>🔐 {t('title')}</CardTitle>
          </CardHeader>
          <CardContent>
            {/* Region Selection */}
            {!selectedRegion ? (
              <>
                <p className="text-muted-foreground mb-6">{t('selectRegion')}</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-md mx-auto">
                  <Button
                    variant="outline"
                    className="h-24 text-lg"
                    onClick={() => handleRegionSelect('US')}
                  >
                    🇺🇸 {t('usa')}
                  </Button>
                  <Button
                    variant="outline"
                    className="h-24 text-lg"
                    onClick={() => handleRegionSelect('EU')}
                  >
                    🇪🇺 {t('europe')}
                  </Button>
                </div>
              </>
            ) : !selectedState ? (
              <>
                {/* State Selection */}
                <div className="mb-6">
                  <Button
                    variant="outline"
                    onClick={() => setSelectedRegion(null)}
                  >
                    ← {t('selectRegion')}
                  </Button>
                  <span className="ml-4 text-lg font-medium">
                    {selectedRegion === 'US' ? t('usa') : t('europe')}
                  </span>
                </div>

                <p className="text-muted-foreground mb-4">{t('selectState')}</p>

                {isLoadingStates ? (
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                    {[...Array(8)].map((_, i) => (
                      <Skeleton key={i} className="h-12" />
                    ))}
                  </div>
                ) : states && states.length > 0 ? (
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                    {states.map((state) => (
                      <Button
                        key={state.state}
                        variant="outline"
                        onClick={() => handleStateSelect(state.state)}
                        className="h-auto py-3"
                      >
                        <div className="text-center w-full">
                          <div className="font-medium">{state.state}</div>
                          <div className="text-xs text-muted-foreground">
                            {state.count} {state.count === 1 ? 'proxy' : 'proxies'}
                          </div>
                        </div>
                      </Button>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    {t('regionNotFound')}
                  </div>
                )}
              </>
            ) : (
              <>
                {/* Products List */}
                <div className="mb-6 flex items-center gap-4">
                  <Button
                    variant="outline"
                    onClick={() => setSelectedState(null)}
                  >
                    ← {t('selectState')}
                  </Button>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">
                      {selectedRegion === 'US' ? t('usa') : t('europe')}
                    </Badge>
                    <span className="text-muted-foreground">/</span>
                    <Badge variant="default">{selectedState}</Badge>
                  </div>
                </div>

                {isLoadingProducts ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {[...Array(6)].map((_, i) => (
                      <Skeleton key={i} className="h-48" />
                    ))}
                  </div>
                ) : products && products.products.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {products.products.map((product) => (
                      <Card key={product.product_id}>
                        <CardContent className="pt-6">
                          <div className="space-y-3">
                            <div className="flex justify-between items-start">
                              <div>
                                <Badge variant="secondary" className="mb-2">PPTP</Badge>
                                <p className="text-sm font-medium">{product.state}</p>
                                {product.city && (
                                  <p className="text-xs text-muted-foreground">{product.city}</p>
                                )}
                              </div>
                              <div className="text-right">
                                <div className="text-2xl font-bold">{product.price}$</div>
                                <div className="text-xs text-muted-foreground">24h</div>
                              </div>
                            </div>

                            {product.isp && (
                              <div className="text-xs">
                                <span className="text-muted-foreground">ISP:</span>
                                <span className="ml-1">{product.isp}</span>
                              </div>
                            )}

                            <Button
                              className="w-full"
                              onClick={() => handleBuyClick(product)}
                            >
                              {t('buy')}
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <p className="text-muted-foreground mb-4">{t('regionNotFound')}</p>
                    <p className="text-sm text-muted-foreground">{t('tryOtherSettings')}</p>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Purchase Dialog */}
      <Dialog open={purchaseDialogOpen} onOpenChange={setPurchaseDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('buy')} PPTP</DialogTitle>
            <DialogDescription>
              Подтверждение покупки PPTP прокси
            </DialogDescription>
          </DialogHeader>
          
          {selectedProduct && (
            <div className="space-y-4 py-4">
              <div className="bg-muted p-3 rounded space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Регион:</span>
                  <span className="font-medium">
                    {selectedRegion === 'US' ? t('usa') : t('europe')}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Штат:</span>
                  <span className="font-medium">{selectedProduct.state}</span>
                </div>
                {selectedProduct.city && (
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Город:</span>
                    <span className="font-medium">{selectedProduct.city}</span>
                  </div>
                )}
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Цена:</span>
                  <span className="font-medium">{selectedProduct.price}$</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Срок:</span>
                  <span className="font-medium">24 часа</span>
                </div>
              </div>

              <div>
                <label htmlFor="coupon" className="text-sm font-medium mb-2 block">
                  Код купона (необязательно):
                </label>
                <Input
                  id="coupon"
                  type="text"
                  placeholder="PROMO2024"
                  value={couponCode}
                  onChange={(e) => setCouponCode(e.target.value)}
                />
              </div>

              <div className="bg-primary/10 p-3 rounded">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Итого:</span>
                  <span className="text-2xl font-bold">{selectedProduct.price}$</span>
                </div>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setPurchaseDialogOpen(false)}>
              Отмена
            </Button>
            <Button 
              onClick={handlePurchaseConfirm} 
              disabled={purchaseMutation.isPending}
            >
              {purchaseMutation.isPending ? 'Покупка...' : 'Подтвердить покупку'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
