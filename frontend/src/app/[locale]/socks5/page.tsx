/**
 * SOCKS5 Catalog page
 * Browse and purchase SOCKS5 proxies with filters and purchase dialog
 */

'use client';

import { useState } from 'react';
import { useSocks5Products, usePurchaseSocks5 } from '@/hooks/use-api';
import { useTranslations } from 'next-intl';
import { Navbar } from '@/components/layout/navbar';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { CountrySelector } from '@/components/country-selector';
import { ProxyCard } from '@/components/proxy-card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { X } from 'lucide-react';

export default function Socks5Page() {
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const t = useTranslations('socks5');

  // Filter states
  const [filterType, setFilterType] = useState<'state' | 'city' | 'zip' | 'random'>('random');
  const [stateFilter, setStateFilter] = useState('');
  const [cityFilter, setCityFilter] = useState('');
  const [zipFilter, setZipFilter] = useState('');

  // Purchase dialog states
  const [purchaseDialogOpen, setPurchaseDialogOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<any>(null);
  const [quantity, setQuantity] = useState('1');
  const [couponCode, setCouponCode] = useState('');

  const { data: products, isLoading } = useSocks5Products(
    {
      country: selectedCountry || '',
      state: filterType === 'state' ? stateFilter : undefined,
      city: filterType === 'city' ? cityFilter : undefined,
      zip: filterType === 'zip' ? zipFilter : undefined,
      random: filterType === 'random',
      page,
      page_size: 10
    },
    {
      enabled: !!selectedCountry
    }
  );

  const purchaseMutation = usePurchaseSocks5();

  const handleBuyClick = (product: any) => {
    setSelectedProduct(product);
    setPurchaseDialogOpen(true);
  };

  const handlePurchaseConfirm = () => {
    if (selectedProduct) {
      purchaseMutation.mutate({
        product_id: selectedProduct.product_id,
        quantity: parseInt(quantity) || 1,
        coupon_code: couponCode || undefined
      });
      setPurchaseDialogOpen(false);
      setQuantity('1');
      setCouponCode('');
    }
  };

  const calculateTotalPrice = () => {
    if (!selectedProduct || !quantity) return '0.00';
    const qty = parseInt(quantity) || 1;
    const basePrice = parseFloat(selectedProduct.price) || 0;
    return (basePrice * qty).toFixed(2);
  };

  const resetFilters = () => {
    setStateFilter('');
    setCityFilter('');
    setZipFilter('');
  };

  return (
    <>
      <Navbar />
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardHeader>
            <CardTitle>🧦 {t('title')}</CardTitle>
          </CardHeader>
          <CardContent>
            {!selectedCountry ? (
              <>
                <p className="text-muted-foreground mb-6">{t('selectCountry')}</p>
                <CountrySelector
                  onSelect={setSelectedCountry}
                  proxyType="SOCKS5"
                />
              </>
            ) : (
              <>
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-4">
                    <Button
                      variant="outline"
                      onClick={() => {
                        setSelectedCountry(null);
                        resetFilters();
                      }}
                    >
                      ← {t('selectCountry')}
                    </Button>
                    <span className="text-lg font-medium">{selectedCountry}</span>
                  </div>
                </div>

                {/* Filters Panel */}
                <Card className="mb-6">
                  <CardContent className="pt-6">
                    <p className="text-sm font-medium mb-3">{t('filters')}:</p>
                    
                    <Tabs value={filterType} onValueChange={(v) => {
                      setFilterType(v as any);
                      resetFilters();
                    }}>
                      <TabsList className="grid w-full grid-cols-4">
                        <TabsTrigger value="state">{t('state')}</TabsTrigger>
                        <TabsTrigger value="city">{t('city')}</TabsTrigger>
                        <TabsTrigger value="zip">{t('zip')}</TabsTrigger>
                        <TabsTrigger value="random">{t('random')}</TabsTrigger>
                      </TabsList>

                      <TabsContent value="state" className="space-y-3">
                        <Input
                          placeholder={t('state')}
                          value={stateFilter}
                          onChange={(e) => setStateFilter(e.target.value)}
                        />
                        {stateFilter && (
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary">
                              {t('state')}: {stateFilter}
                              <button
                                onClick={() => setStateFilter('')}
                                className="ml-2 hover:text-destructive"
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </Badge>
                          </div>
                        )}
                      </TabsContent>

                      <TabsContent value="city" className="space-y-3">
                        <Input
                          placeholder={t('cityLabel')}
                          value={cityFilter}
                          onChange={(e) => setCityFilter(e.target.value)}
                        />
                        {cityFilter && (
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary">
                              {t('city')}: {cityFilter}
                              <button
                                onClick={() => setCityFilter('')}
                                className="ml-2 hover:text-destructive"
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </Badge>
                          </div>
                        )}
                      </TabsContent>

                      <TabsContent value="zip" className="space-y-3">
                        <Input
                          placeholder={t('zipLabel')}
                          value={zipFilter}
                          onChange={(e) => setZipFilter(e.target.value)}
                        />
                        {zipFilter && (
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary">
                              {t('zip')}: {zipFilter}
                              <button
                                onClick={() => setZipFilter('')}
                                className="ml-2 hover:text-destructive"
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </Badge>
                          </div>
                        )}
                      </TabsContent>

                      <TabsContent value="random">
                        <p className="text-sm text-muted-foreground">
                          Показываются случайные прокси из выбранной страны
                        </p>
                      </TabsContent>
                    </Tabs>
                  </CardContent>
                </Card>

                {/* Products Grid */}
                {isLoading ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {[...Array(6)].map((_, i) => (
                      <Skeleton key={i} className="h-64" />
                    ))}
                  </div>
                ) : products && products.products.length > 0 ? (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {products.products.map((proxy) => (
                        <ProxyCard
                          key={proxy.product_id}
                          proxy={proxy}
                          onBuy={handleBuyClick}
                        />
                      ))}
                    </div>

                    {products.has_more && (
                      <div className="mt-6 text-center">
                        <Button onClick={() => setPage(page + 1)}>
                          {t('showMore')}
                        </Button>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    {filterType === 'state' && t('regionNotFound')}
                    {filterType === 'city' && t('cityNotFound')}
                    {filterType === 'zip' && t('zipNotFound')}
                    {filterType === 'random' && t('regionNotFound')}
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
            <DialogTitle>{t('buyProxy')}</DialogTitle>
            <DialogDescription>
              Подтверждение покупки прокси
            </DialogDescription>
          </DialogHeader>
          
          {selectedProduct && (
            <div className="space-y-4 py-4">
              <div className="bg-muted p-3 rounded space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{t('country')}:</span>
                  <span className="font-medium">{selectedProduct.country}</span>
                </div>
                {selectedProduct.state && (
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">{t('state')}:</span>
                    <span className="font-medium">{selectedProduct.state}</span>
                  </div>
                )}
                {selectedProduct.city && (
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">{t('city')}:</span>
                    <span className="font-medium">{selectedProduct.city}</span>
                  </div>
                )}
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{t('price')}:</span>
                  <span className="font-medium">{selectedProduct.price}$</span>
                </div>
              </div>

              <div>
                <label htmlFor="quantity" className="text-sm font-medium mb-2 block">
                  {t('quantity')}:
                </label>
                <Input
                  id="quantity"
                  type="number"
                  min="1"
                  max="100"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                />
              </div>

              <div>
                <label htmlFor="coupon" className="text-sm font-medium mb-2 block">
                  {t('couponCode')} (необязательно):
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
                  <span className="text-sm font-medium">{t('totalPrice')}:</span>
                  <span className="text-2xl font-bold">{calculateTotalPrice()}$</span>
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
              disabled={purchaseMutation.isPending || !quantity}
            >
              {purchaseMutation.isPending ? 'Покупка...' : t('confirmPurchase')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
