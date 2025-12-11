/**
 * ProxyCard component
 * Displays proxy details in catalog with buy button
 */

'use client';

import { ProxyItem } from '@/types/api';
import { useTranslations } from 'next-intl';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { formatDate } from '@/lib/utils';
import { Server, Globe, MapPin, Zap, Hash, Calendar } from 'lucide-react';

interface ProxyCardProps {
  proxy: ProxyItem;
  onBuy: (productId: number) => void;
  showPrice?: boolean;
}

/**
 * ProxyCard component for displaying proxy in catalog
 * Shows all proxy details including ISP, location, speed, etc.
 */
export function ProxyCard({ proxy, onBuy, showPrice = true }: ProxyCardProps) {
  const t = useTranslations('socks5');

  return (
    <Card className="hover:border-primary transition-colors hover:shadow-md">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">
            🪄 {t('ip')} {proxy.ip}
          </CardTitle>
          {proxy.port && (
            <Badge variant="outline">{t('port')}: {proxy.port}</Badge>
          )}
        </div>
      </CardHeader>

      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          {proxy.ISP && (
            <div className="flex items-center gap-2">
              <Server className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">{t('isp')}:</span>
              <span className="font-medium">{proxy.ISP}</span>
            </div>
          )}

          {proxy.ORG && (
            <div className="flex items-center gap-2">
              <Server className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">{t('org')}:</span>
              <span className="font-medium">{proxy.ORG}</span>
            </div>
          )}

          {proxy.city && (
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">{t('cityLabel')}:</span>
              <span className="font-medium">{proxy.city}</span>
            </div>
          )}

          {proxy.state && (
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">{t('region')}:</span>
              <span className="font-medium">{proxy.state}</span>
            </div>
          )}

          {proxy.speed && (
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">{t('speed')}:</span>
              <span className="font-medium">{proxy.speed}</span>
            </div>
          )}

          {proxy.zip && (
            <div className="flex items-center gap-2">
              <Hash className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">{t('zipLabel')}:</span>
              <span className="font-medium">{proxy.zip}</span>
            </div>
          )}

          <div className="flex items-center gap-2">
            <Globe className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">{t('country')}:</span>
            <span className="font-medium">{proxy.country}</span>
          </div>

          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">{t('added')}:</span>
            <span className="font-medium">{formatDate(proxy.datestamp)}</span>
          </div>
        </div>
      </CardContent>

      <CardFooter className="flex items-center justify-between">
        {showPrice && (
          <Badge variant="default" className="text-lg px-4 py-2">
            {proxy.price}$
          </Badge>
        )}
        <Button 
          onClick={() => onBuy(proxy.product_id)}
          className="flex-1 ml-4"
        >
          💳 {t('buyProxy')}
        </Button>
      </CardFooter>
    </Card>
  );
}

