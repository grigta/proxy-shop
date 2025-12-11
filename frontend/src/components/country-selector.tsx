/**
 * CountrySelector component
 * Displays countries in 4 pages with pagination
 */

'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { COUNTRIES_PAGES } from '@/lib/constants';

interface CountrySelectorProps {
  onSelect: (country: string) => void;
  proxyType: 'socks5' | 'pptp';
}

/**
 * CountrySelector component with pagination
 * Shows 4 pages of countries from architecture_bot.md
 */
export function CountrySelector({ onSelect, proxyType }: CountrySelectorProps) {
  const t = useTranslations('common');
  const [currentPage, setCurrentPage] = useState(0);

  const currentCountries = COUNTRIES_PAGES[currentPage];
  const totalPages = COUNTRIES_PAGES.length;

  return (
    <div className="space-y-6">
      {/* Countries Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
        {currentCountries.map((country) => (
          <Button
            key={country.code}
            variant="outline"
            className="justify-start h-auto py-3 text-left"
            onClick={() => onSelect(country.name)}
          >
            <span className="text-2xl mr-2">{country.flag}</span>
            <span>{country.name}</span>
          </Button>
        ))}
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center justify-center gap-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
          disabled={currentPage === 0}
        >
          <ChevronLeft className="h-4 w-4 mr-1" />
          {t('back')}
        </Button>

        <span className="text-sm text-muted-foreground">
          Страница {currentPage + 1} из {totalPages}
        </span>

        <Button
          variant="outline"
          size="sm"
          onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
          disabled={currentPage === totalPages - 1}
        >
          Вперед
          <ChevronRight className="h-4 w-4 ml-1" />
        </Button>
      </div>
    </div>
  );
}

