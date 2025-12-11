import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check } from 'lucide-react';
import { CountryListItem } from '@/types/api';

interface CountrySelectProps {
  countries: CountryListItem[];
  value: string;
  onChange: (country: string) => void;
  disabled?: boolean;
}

export const CountrySelect: React.FC<CountrySelectProps> = ({
  countries,
  value,
  onChange,
  disabled = false
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const selectedCountry = countries.find(c => c.country === value);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleSelect = (country: string) => {
    onChange(country);
    setIsOpen(false);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Selected value button */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className="w-full bg-gray-50 dark:bg-[#27272a] border border-gray-200 dark:border-[#3f3f46] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black dark:focus:ring-white text-gray-900 dark:text-white transition-colors disabled:opacity-50 flex items-center justify-between gap-2"
      >
        <span className="flex items-center gap-2 truncate">
          {selectedCountry ? (
            <>
              <span className="text-xl leading-none">{selectedCountry.flag}</span>
              <span className="truncate">{selectedCountry.country}</span>
              <span className="text-gray-500 dark:text-gray-400">({selectedCountry.available_count})</span>
            </>
          ) : (
            <span className="text-gray-400">Select country...</span>
          )}
        </span>
        <ChevronDown
          size={16}
          className={`flex-shrink-0 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Dropdown menu */}
      {isOpen && !disabled && (
        <div className="absolute z-50 w-full mt-1 bg-white dark:bg-[#27272a] border border-gray-200 dark:border-[#3f3f46] rounded-lg shadow-lg max-h-64 overflow-y-auto">
          {countries.length === 0 ? (
            <div className="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">
              Loading...
            </div>
          ) : (
            countries.map((country) => (
              <button
                key={country.country_code}
                type="button"
                onClick={() => handleSelect(country.country)}
                className="w-full px-3 py-2 text-sm text-left hover:bg-gray-100 dark:hover:bg-[#3f3f46] transition-colors flex items-center gap-2 group"
              >
                <span className="text-xl leading-none flex-shrink-0">{country.flag}</span>
                <span className="flex-1 truncate text-gray-900 dark:text-white">
                  {country.country}
                </span>
                <span className="text-gray-500 dark:text-gray-400 text-xs">
                  ({country.available_count})
                </span>
                {country.country === value && (
                  <Check size={16} className="text-black dark:text-white flex-shrink-0" />
                )}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
};
