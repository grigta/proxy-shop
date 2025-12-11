import React, { useState, useMemo, useEffect } from 'react';
import { Search, Signal, SignalHigh, SignalLow, Loader2, ChevronDown, Copy, Check, AlertCircle, CheckCircle, X } from 'lucide-react';
import { SpeedLevel } from '../types';
import { apiClient } from '@/lib/api-client';
import { ProxyItem, CountryListItem, ProxyType } from '@/types/api';
import { DEFAULT_PAGE_SIZE } from '@/lib/constants';
import { usePurchaseFlow } from '../hooks/usePurchaseFlow';
import { CountrySelect } from '../components/CountrySelect';


const Socks: React.FC = () => {
  // Use purchase flow hook
  const {
    user,
    selectedProxy,
    modalState,
    couponCode,
    setCouponCode,
    purchasing,
    purchaseResponse,
    errorMessage,
    copiedField,
    handleBuyClick,
    handlePurchase,
    handleCopy,
    closeModal,
  } = usePurchaseFlow({
    purchaseFunction: async (proxy, couponCode) => {
      return await apiClient.purchaseSocks5({
        product_id: proxy.product_id,
        quantity: 1,
        coupon_code: couponCode,
      });
    },
    unavailableMessageSocks: 'Proxy is no longer available. Please try another one.',
    unavailableMessagePptp: 'No PPTP servers available in this location. Please try another location.',
    proxyType: 'socks',
  });

  // State for proxies and countries
  const [proxies, setProxies] = useState<ProxyItem[]>([]);
  const [countries, setCountries] = useState<CountryListItem[]>([]);
  
  // Draft filter states (for input fields)
  const [draftState, setDraftState] = useState<string>('');
  const [draftCity, setDraftCity] = useState<string>('');
  const [draftZip, setDraftZip] = useState<string>('');
  
  // Applied filter states (used in API requests)
  const [selectedCountry, setSelectedCountry] = useState<string>('');
  const [selectedState, setSelectedState] = useState<string>('');
  const [selectedCity, setSelectedCity] = useState<string>('');
  const [selectedZip, setSelectedZip] = useState<string>('');
  const [filterSpeed, setFilterSpeed] = useState<string>('All');
  
  // Loading and error states
  const [loading, setLoading] = useState<boolean>(false);
  const [countriesError, setCountriesError] = useState<string | null>(null);
  const [productsError, setProductsError] = useState<string | null>(null);
  
  // Pagination states
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(DEFAULT_PAGE_SIZE);
  const [total, setTotal] = useState<number>(0);
  const [hasMore, setHasMore] = useState<boolean>(false);

  // Load countries on mount
  useEffect(() => {
    const loadCountries = async () => {
      setCountriesError(null);
      try {
        const data = await apiClient.getCountries(ProxyType.SOCKS5);
        setCountries(data);
        // Set default country to first available or United States
        if (data.length > 0) {
          const usCountry = data.find(c => c.country === 'United States');
          setSelectedCountry(usCountry?.country || data[0].country);
        }
      } catch (err: any) {
        console.error('Error loading countries:', err);
        setCountriesError(err.response?.data?.detail || 'Failed to load countries');
      }
    };
    loadCountries();
  }, []);

  // Load proxies when filters or pagination change
  useEffect(() => {
    if (!selectedCountry) return; // Wait for country to be set

    const loadProxies = async () => {
      setLoading(true);
      setProductsError(null);
      try {
        const response = await apiClient.getSocks5Products({
          country: selectedCountry,
          state: selectedState || undefined,
          city: selectedCity || undefined,
          zip: selectedZip || undefined,
          page,
          page_size: pageSize,
        });
        setProxies(response.products);
        setTotal(response.total);
        setHasMore(response.has_more);
      } catch (err: any) {
        console.error('Error loading proxies:', err);
        setProductsError(err.response?.data?.detail || 'Failed to load proxies');
        setProxies([]);
      } finally {
        setLoading(false);
      }
    };
    loadProxies();
  }, [selectedCountry, selectedState, selectedCity, selectedZip, page, pageSize]);

  // Handle search button click
  const handleSearch = () => {
    // Apply draft values to selected filters
    setSelectedState(draftState);
    setSelectedCity(draftCity);
    setSelectedZip(draftZip);
    setPage(1); // Reset to first page when filters change
  };

  // Client-side speed filtering
  const processedProxies = useMemo(() => {
    return proxies.filter(proxy => {
      if (filterSpeed === 'All') return true;
      // Map proxy.speed to SpeedLevel if needed
      return proxy.speed === filterSpeed;
    });
  }, [proxies, filterSpeed]);

  const SpeedIcon = ({ speed }: { speed: string | null | undefined }) => {
    if (speed === SpeedLevel.FAST || speed === 'Fast') return <SignalHigh size={16} className="text-green-600 dark:text-green-500" />;
    if (speed === SpeedLevel.MODERATE || speed === 'Moderate') return <Signal size={16} className="text-yellow-600 dark:text-yellow-500" />;
    if (speed === SpeedLevel.SLOW || speed === 'Slow') return <SignalLow size={16} className="text-red-600 dark:text-red-500" />;
    return <Signal size={16} className="text-gray-500 dark:text-gray-400" />;
  };

  // Helper to mask IP
  const formatMaskedIP = (ip: string) => {
    const parts = ip.split('.');
    if (parts.length >= 2) {
      return `${parts[0]}.${parts[1]}.*.*`;
    }
    return ip;
  };

  return (
    <div className="p-6 bg-gray-50 dark:bg-[#09090b] min-h-full transition-colors duration-200">
      {/* Error Message for Countries */}
      {countriesError && (
        <div className="mb-4 p-4 bg-red-100 dark:bg-red-900/20 border border-red-300 dark:border-red-800 rounded-lg text-red-800 dark:text-red-300">
          {countriesError}
        </div>
      )}

      {/* Top Controls */}
      <div className="bg-white dark:bg-[#18181b] p-4 rounded-xl border border-gray-200 dark:border-[#27272a] shadow-sm mb-6 transition-colors duration-200">
        <div className="flex flex-col md:flex-row gap-4 items-end">
            <div className="flex-1 grid grid-cols-2 md:grid-cols-5 gap-4 w-full">
                <div>
                    <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1 block">Country</label>
                    <CountrySelect
                      countries={countries}
                      value={selectedCountry}
                      onChange={(country) => {
                        setSelectedCountry(country);
                        setPage(1);
                      }}
                      disabled={loading}
                    />
                </div>
                <div>
                    <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1 block">State</label>
                    <input 
                      type="text" 
                      placeholder="NY" 
                      value={draftState}
                      onChange={(e) => setDraftState(e.target.value)}
                      disabled={loading}
                      className="w-full bg-gray-50 dark:bg-[#27272a] border border-gray-200 dark:border-[#3f3f46] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black dark:focus:ring-white text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 transition-colors disabled:opacity-50" 
                    />
                </div>
                <div>
                    <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1 block">City</label>
                    <input 
                      type="text" 
                      placeholder="New York" 
                      value={draftCity}
                      onChange={(e) => setDraftCity(e.target.value)}
                      disabled={loading}
                      className="w-full bg-gray-50 dark:bg-[#27272a] border border-gray-200 dark:border-[#3f3f46] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black dark:focus:ring-white text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 transition-colors disabled:opacity-50" 
                    />
                </div>
                <div>
                    <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1 block">Zip</label>
                    <input 
                      type="text" 
                      placeholder="10001" 
                      value={draftZip}
                      onChange={(e) => setDraftZip(e.target.value)}
                      disabled={loading}
                      className="w-full bg-gray-50 dark:bg-[#27272a] border border-gray-200 dark:border-[#3f3f46] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black dark:focus:ring-white text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 transition-colors disabled:opacity-50" 
                    />
                </div>
                <div>
                    <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1 block">Zip Radius</label>
                    <select 
                      disabled
                      className="w-full bg-gray-50 dark:bg-[#27272a] border border-gray-200 dark:border-[#3f3f46] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black dark:focus:ring-white text-gray-900 dark:text-white transition-colors opacity-50"
                    >
                        <option>None</option>
                        <option>10 miles</option>
                        <option>50 miles</option>
                    </select>
                </div>
            </div>
            <button 
              onClick={handleSearch}
              disabled={loading}
              className="bg-gray-100 dark:bg-[#27272a] hover:bg-gray-200 dark:hover:bg-[#3f3f46] p-2 rounded-lg transition-colors border border-gray-200 dark:border-[#3f3f46] h-[38px] w-[38px] flex items-center justify-center flex-shrink-0 disabled:opacity-50"
            >
                {loading ? <Loader2 size={20} className="text-gray-600 dark:text-gray-300 animate-spin" /> : <Search size={20} className="text-gray-600 dark:text-gray-300" />}
            </button>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="flex justify-between items-center gap-2 mb-4">
        <div className="text-xs text-gray-500 dark:text-gray-400 italic">
          * Фильтр скорости применяется к текущей странице
        </div>
        <div className="flex items-center gap-2 bg-white dark:bg-[#18181b] border border-gray-200 dark:border-[#27272a] rounded-lg px-3 py-1.5 transition-colors">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Speed</span>
            <div className="relative">
              <select 
                value={filterSpeed}
                onChange={(e) => setFilterSpeed(e.target.value)}
                disabled={loading}
                className="text-xs font-semibold pl-2 pr-6 py-0.5 rounded bg-gray-100 dark:bg-[#27272a] text-gray-900 dark:text-white transition-colors appearance-none focus:outline-none cursor-pointer border-none disabled:opacity-50"
              >
                <option value="All">All</option>
                {Object.values(SpeedLevel).map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
              <ChevronDown size={12} className="absolute right-1.5 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" />
            </div>
        </div>
      </div>

      {/* Data Table */}
      <div className="bg-white dark:bg-[#18181b] border border-gray-200 dark:border-[#27272a] rounded-xl shadow-sm overflow-hidden transition-colors duration-200">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-500 dark:text-gray-400 uppercase bg-gray-50 dark:bg-[#27272a] border-b border-gray-200 dark:border-[#3f3f46]">
              <tr>
                <th className="px-6 py-3 font-medium">Proxy IP</th>
                <th className="px-6 py-3 font-medium">Country</th>
                <th className="px-6 py-3 font-medium">City</th>
                <th className="px-6 py-3 font-medium">State</th>
                <th className="px-6 py-3 font-medium">ISP</th>
                <th className="px-6 py-3 font-medium">Speed</th>
                <th className="px-6 py-3 font-medium text-right">Buy</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-[#27272a]">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                    <div className="flex items-center justify-center gap-2">
                      <Loader2 size={20} className="animate-spin" />
                      <span>Loading proxies...</span>
                    </div>
                  </td>
                </tr>
              ) : processedProxies.length > 0 ? (
                processedProxies.map((proxy) => (
                  <tr key={proxy.product_id} className="hover:bg-gray-50 dark:hover:bg-[#27272a] transition-colors text-gray-900 dark:text-gray-300">
                    <td className="px-6 py-4 font-mono text-gray-700 dark:text-gray-300">{formatMaskedIP(proxy.ip)}</td>
                    <td className="px-6 py-4">{proxy.country}</td>
                    <td className="px-6 py-4">{proxy.city || 'N/A'}</td>
                    <td className="px-6 py-4">{proxy.state || 'N/A'}</td>
                    <td className="px-6 py-4 truncate max-w-[150px]" title={proxy.ISP}>{proxy.ISP || 'N/A'}</td>
                    <td className="px-6 py-4">
                      {proxy.speed ? (
                        <div className="flex items-center gap-2">
                          <SpeedIcon speed={proxy.speed} />
                          <span className="text-xs font-medium">{proxy.speed}</span>
                        </div>
                      ) : (
                        <span className="text-xs text-gray-400">N/A</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button 
                        onClick={() => handleBuyClick(proxy)}
                        disabled={loading}
                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-white dark:bg-[#18181b] border border-gray-200 dark:border-[#3f3f46] rounded-lg text-xs font-medium hover:bg-black dark:hover:bg-white hover:text-white dark:hover:text-black hover:border-black dark:hover:border-white transition-all text-gray-900 dark:text-gray-100 disabled:opacity-50"
                      >
                          <span>${parseFloat(proxy.price).toFixed(2)}</span>
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                    {productsError ? 'Failed to load proxies. Please try again.' : 'No proxies found matching your filters.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="px-6 py-4 border-t border-gray-200 dark:border-[#27272a] bg-gray-50 dark:bg-[#18181b] flex justify-between items-center transition-colors">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Показано {processedProxies.length} прокси на странице {page} (всего доступно {total} без учёта фильтра скорости)
            </span>
            <div className="flex gap-2">
                <button 
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={loading || page === 1}
                  className="px-3 py-1 border border-gray-300 dark:border-[#3f3f46] rounded text-xs bg-white dark:bg-[#27272a] text-gray-900 dark:text-gray-200 disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-[#3f3f46] transition-colors"
                >
                  Previous
                </button>
                <button 
                  onClick={() => setPage(p => p + 1)}
                  disabled={loading || !hasMore}
                  className="px-3 py-1 border border-gray-300 dark:border-[#3f3f46] rounded text-xs bg-white dark:bg-[#27272a] text-gray-900 dark:text-gray-200 disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-[#3f3f46] transition-colors"
                >
                  Next
                </button>
            </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {modalState === 'confirm' && selectedProxy && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-[#18181b] border border-gray-200 dark:border-[#27272a] rounded-xl shadow-2xl max-w-md w-full mx-4 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Confirm Purchase</h2>
              <button 
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4">
              {/* Proxy Details */}
              <div className="bg-gray-50 dark:bg-[#27272a] rounded-lg p-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500 dark:text-gray-400">IP:</span>
                  <span className="font-mono text-gray-900 dark:text-white">{formatMaskedIP(selectedProxy.ip)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500 dark:text-gray-400">Country:</span>
                  <span className="text-gray-900 dark:text-white">{selectedProxy.country}</span>
                </div>
                {selectedProxy.state && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500 dark:text-gray-400">State:</span>
                    <span className="text-gray-900 dark:text-white">{selectedProxy.state}</span>
                  </div>
                )}
                {selectedProxy.city && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500 dark:text-gray-400">City:</span>
                    <span className="text-gray-900 dark:text-white">{selectedProxy.city}</span>
                  </div>
                )}
                {selectedProxy.ISP && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500 dark:text-gray-400">ISP:</span>
                    <span className="text-gray-900 dark:text-white">{selectedProxy.ISP}</span>
                  </div>
                )}
                {selectedProxy.speed && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500 dark:text-gray-400">Speed:</span>
                    <span className="text-gray-900 dark:text-white">{selectedProxy.speed}</span>
                  </div>
                )}
              </div>

              {/* Price and Balance */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500 dark:text-gray-400">Price:</span>
                  <span className="text-lg font-bold text-gray-900 dark:text-white">${parseFloat(selectedProxy.price).toFixed(2)}</span>
                </div>
                {user && (
                  <>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500 dark:text-gray-400">Current Balance:</span>
                      <span className="text-gray-900 dark:text-white">${parseFloat(user.balance).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm font-semibold">
                      <span className="text-gray-500 dark:text-gray-400">Balance After:</span>
                      <span className={`${parseFloat(user.balance) >= parseFloat(selectedProxy.price) ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'}`}>
                        ${(parseFloat(user.balance) - parseFloat(selectedProxy.price)).toFixed(2)}
                      </span>
                    </div>
                  </>
                )}
              </div>

              {/* Coupon Code Input */}
              <div>
                <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1 block">Coupon Code (Optional)</label>
                <input 
                  type="text"
                  value={couponCode}
                  onChange={(e) => setCouponCode(e.target.value)}
                  placeholder="Enter coupon code"
                  disabled={purchasing}
                  className="w-full bg-gray-50 dark:bg-[#27272a] border border-gray-200 dark:border-[#3f3f46] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black dark:focus:ring-white text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 transition-colors disabled:opacity-50"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={closeModal}
                  disabled={purchasing}
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-[#3f3f46] rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-[#27272a] transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handlePurchase}
                  disabled={purchasing || (user && parseFloat(user.balance) < parseFloat(selectedProxy.price))}
                  className="flex-1 px-4 py-2 bg-black dark:bg-white text-white dark:text-black rounded-lg text-sm font-medium hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {purchasing ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      <span>Processing...</span>
                    </>
                  ) : (
                    'Purchase'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Success Modal */}
      {modalState === 'success' && purchaseResponse && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-[#18181b] border border-gray-200 dark:border-[#27272a] rounded-xl shadow-2xl max-w-md w-full mx-4 p-6">
            <div className="flex items-center justify-center mb-4">
              <div className="bg-green-100 dark:bg-green-900/20 rounded-full p-3">
                <CheckCircle size={32} className="text-green-600 dark:text-green-500" />
              </div>
            </div>

            <h2 className="text-xl font-bold text-center text-gray-900 dark:text-white mb-2">Purchase Successful!</h2>
            
            {purchaseResponse.order_id && (
              <p className="text-sm text-center text-gray-500 dark:text-gray-400 mb-4">
                Order ID: {purchaseResponse.order_id}
              </p>
            )}

            <div className="space-y-4">
              {/* Proxy Credentials */}
              {purchaseResponse.proxies && purchaseResponse.proxies.length > 0 && (
                <div className="bg-gray-50 dark:bg-[#27272a] rounded-lg p-4 space-y-3">
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Proxy Details</h3>
                  
                  {/* IP:Port */}
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs text-gray-500 dark:text-gray-400">IP:Port</span>
                      <button
                        onClick={() => handleCopy('ip', `${purchaseResponse.proxies[0].ip}${purchaseResponse.proxies[0].port ? ':' + purchaseResponse.proxies[0].port : ''}`)}
                        className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 flex items-center gap-1"
                      >
                        {copiedField === 'ip' ? <Check size={14} /> : <Copy size={14} />}
                        {copiedField === 'ip' ? 'Copied!' : 'Copy'}
                      </button>
                    </div>
                    <div className="font-mono text-sm text-gray-900 dark:text-white bg-white dark:bg-[#18181b] rounded px-2 py-1 border border-gray-200 dark:border-[#3f3f46]">
                      {purchaseResponse.proxies[0].ip}{purchaseResponse.proxies[0].port && `:${purchaseResponse.proxies[0].port}`}
                    </div>
                  </div>

                  {/* Login */}
                  {purchaseResponse.proxies[0].login && (
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-xs text-gray-500 dark:text-gray-400">Login</span>
                        <button
                          onClick={() => handleCopy('login', purchaseResponse.proxies[0].login)}
                          className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 flex items-center gap-1"
                        >
                          {copiedField === 'login' ? <Check size={14} /> : <Copy size={14} />}
                          {copiedField === 'login' ? 'Copied!' : 'Copy'}
                        </button>
                      </div>
                      <div className="font-mono text-sm text-gray-900 dark:text-white bg-white dark:bg-[#18181b] rounded px-2 py-1 border border-gray-200 dark:border-[#3f3f46]">
                        {purchaseResponse.proxies[0].login}
                      </div>
                    </div>
                  )}

                  {/* Password */}
                  {purchaseResponse.proxies[0].password && (
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-xs text-gray-500 dark:text-gray-400">Password</span>
                        <button
                          onClick={() => handleCopy('password', purchaseResponse.proxies[0].password)}
                          className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 flex items-center gap-1"
                        >
                          {copiedField === 'password' ? <Check size={14} /> : <Copy size={14} />}
                          {copiedField === 'password' ? 'Copied!' : 'Copy'}
                        </button>
                      </div>
                      <div className="font-mono text-sm text-gray-900 dark:text-white bg-white dark:bg-[#18181b] rounded px-2 py-1 border border-gray-200 dark:border-[#3f3f46]">
                        {purchaseResponse.proxies[0].password}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Expiration and Balance */}
              <div className="bg-gray-50 dark:bg-[#27272a] rounded-lg p-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500 dark:text-gray-400">Expires:</span>
                  <span className="text-gray-900 dark:text-white text-right">
                    {new Date(purchaseResponse.expires_at).toLocaleString()}
                    <span className="text-xs text-gray-500 dark:text-gray-400 ml-1">
                      ({purchaseResponse.hours_left}h left)
                    </span>
                  </span>
                </div>
                <div className="flex justify-between text-sm font-semibold">
                  <span className="text-gray-500 dark:text-gray-400">New Balance:</span>
                  <span className="text-green-600 dark:text-green-500">
                    ${parseFloat(purchaseResponse.new_balance).toFixed(2)}
                  </span>
                </div>
              </div>

              {/* Close Button */}
              <button
                onClick={closeModal}
                className="w-full px-4 py-2 bg-black dark:bg-white text-white dark:text-black rounded-lg text-sm font-medium hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Error Modal */}
      {modalState === 'error' && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-[#18181b] border-2 border-red-300 dark:border-red-800 rounded-xl shadow-2xl max-w-md w-full mx-4 p-6">
            <div className="flex items-center justify-center mb-4">
              <div className="bg-red-100 dark:bg-red-900/20 rounded-full p-3">
                <AlertCircle size={32} className="text-red-600 dark:text-red-500" />
              </div>
            </div>

            <h2 className="text-xl font-bold text-center text-gray-900 dark:text-white mb-4">Purchase Failed</h2>
            
            <div className="bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
              <p className="text-sm text-red-800 dark:text-red-300 text-center">
                {errorMessage}
              </p>
            </div>

            <button
              onClick={closeModal}
              className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Socks;