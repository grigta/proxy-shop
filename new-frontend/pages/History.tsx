import React, { useState, useEffect } from 'react';
import { Search, Copy, Calendar, CheckCircle2, XCircle, Clock, Shield, Server, X } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { useAuth } from '@/AuthContext';
import { copyToClipboard as copyText } from '@/lib/clipboard';
import type { PurchaseHistoryItem, ProxyType } from '@/types/api';
import { AxiosError } from 'axios';

const History: React.FC = () => {
  const { user, updateUser } = useAuth();
  const [filterStatus, setFilterStatus] = useState<'All' | 'Active' | 'Expired'>('All');
  const [searchTerm, setSearchTerm] = useState('');
  const [purchases, setPurchases] = useState<PurchaseHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Extend modal state
  const [extendModal, setExtendModal] = useState<{
    proxyId: number;
    proxyType: ProxyType;
    currentExpiry: string;
    ip?: string;
    port?: string;
  } | null>(null);
  const [extendHours, setExtendHours] = useState(24);
  const [isExtending, setIsExtending] = useState(false);
  const [extendError, setExtendError] = useState<string | null>(null);
  const [extendSuccess, setExtendSuccess] = useState<string | null>(null);

  // Helper function to check if proxy is expired
  const isExpired = (expiresAt: string): boolean => {
    return new Date(expiresAt) < new Date();
  };

  // Fetch purchase history on mount
  useEffect(() => {
    const fetchPurchaseHistory = async () => {
      if (!user?.user_id) return;
      
      setIsLoading(true);
      setError(null);
      
      try {
        const response = await apiClient.getPurchaseHistory(user.user_id);
        setPurchases(response.purchases);
      } catch (err) {
        const axiosError = err as AxiosError<any>;
        setError(axiosError.response?.data?.detail || 'Failed to load purchase history');
        console.error('Failed to fetch purchase history:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPurchaseHistory();
  }, [user?.user_id]);

  // Handle extend proxy
  const handleExtendProxy = async () => {
    if (!extendModal) return;
    
    setIsExtending(true);
    setExtendError(null);
    setExtendSuccess(null);
    
    try {
      // Stage 1: Extend proxy and refresh purchase history
      const response = await apiClient.extendProxy(
        extendModal.proxyId,
        extendModal.proxyType,
        { hours: extendHours }
      );
      
      setExtendSuccess(`Proxy extended successfully! New expiry: ${new Date(response.new_expires_at).toLocaleString()}`);
      
      // Refresh purchase history
      if (user?.user_id) {
        const historyResponse = await apiClient.getPurchaseHistory(user.user_id);
        setPurchases(historyResponse.purchases);
      }
      
      // Stage 2: Try to update user profile (non-critical)
      try {
        const updatedProfile = await apiClient.getProfile();
        updateUser(updatedProfile);
      } catch (profileErr) {
        // Log profile update failure but don't change success state
        console.error('Failed to update user profile after extend (non-critical):', profileErr);
      }
      
      // Close modal after 2 seconds
      setTimeout(() => {
        setExtendModal(null);
        setExtendSuccess(null);
        setExtendHours(24);
      }, 2000);
    } catch (err) {
      const axiosError = err as AxiosError<any>;
      setExtendError(axiosError.response?.data?.detail || 'Failed to extend proxy');
      console.error('Failed to extend proxy:', err);
    } finally {
      setIsExtending(false);
    }
  };

  const filteredData = purchases.filter(item => {
    const expired = isExpired(item.expires_at);
    const status = expired ? 'Expired' : 'Active';
    const matchesStatus = filterStatus === 'All' || status === filterStatus;
    
    // Get first proxy IP for search (check if proxies array has elements)
    const proxyIp = item.proxies.length > 0 ? item.proxies[0]?.ip || '' : '';
    const matchesSearch = proxyIp.includes(searchTerm) || item.country.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesStatus && matchesSearch;
  });

  const copyToClipboard = async (text: string) => {
    await copyText(text);
    // In a real app, show a toast notification here
  };

  return (
    <div className="p-6 bg-gray-50 dark:bg-[#09090b] min-h-full transition-colors duration-200">
      
      {/* Error Display */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Controls */}
      <div className="bg-white dark:bg-[#18181b] p-4 rounded-xl border border-gray-200 dark:border-[#27272a] shadow-sm mb-6 transition-colors duration-200">
        <div className="flex flex-col md:flex-row gap-4 justify-between items-end">
           
           <div className="flex items-center gap-2">
              {/* Status Tabs */}
              <div className="bg-gray-100 dark:bg-[#27272a] p-1 rounded-lg flex">
                 {['All', 'Active', 'Expired'].map((status) => (
                    <button
                        key={status}
                        onClick={() => setFilterStatus(status as any)}
                        className={`px-4 py-1.5 text-xs font-medium rounded-md transition-all ${
                            filterStatus === status 
                            ? 'bg-white dark:bg-[#09090b] text-black dark:text-white shadow-sm' 
                            : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                        }`}
                    >
                        {status}
                    </button>
                 ))}
              </div>
           </div>

           <div className="flex items-center gap-2 w-full md:w-auto">
              <div className="relative w-full md:w-64">
                 <input 
                    type="text" 
                    placeholder="Search IP or Country..." 
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full bg-gray-50 dark:bg-[#27272a] border border-gray-200 dark:border-[#3f3f46] rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black dark:focus:ring-white text-gray-900 dark:text-white placeholder-gray-400 transition-colors" 
                 />
                 <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              </div>
           </div>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black dark:border-white"></div>
        </div>
      )}

      {/* Table */}
      {!isLoading && (
        <div className="bg-white dark:bg-[#18181b] border border-gray-200 dark:border-[#27272a] rounded-xl shadow-sm overflow-hidden transition-colors duration-200">
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-gray-500 dark:text-gray-400 uppercase bg-gray-50 dark:bg-[#27272a] border-b border-gray-200 dark:border-[#3f3f46]">
                <tr>
                  <th className="px-6 py-3 font-medium">Proxy Info</th>
                  <th className="px-6 py-3 font-medium">Location</th>
                  <th className="px-6 py-3 font-medium">Type</th>
                  <th className="px-6 py-3 font-medium">Dates</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                  <th className="px-6 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-[#27272a]">
                {filteredData.length > 0 ? (
                  filteredData.map((item) => {
                    const hasProxies = item.proxies.length > 0;
                    const proxy = hasProxies ? item.proxies[0] : null;
                    const expired = isExpired(item.expires_at);
                    
                    return (
                      <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-[#27272a] transition-colors text-gray-900 dark:text-gray-300">
                        <td className="px-6 py-4">
                            {hasProxies && proxy ? (
                              <div className="flex flex-col">
                                <div className="font-mono font-medium text-gray-900 dark:text-white flex items-center gap-2">
                                    {proxy.ip}:{proxy.port}
                                    <button onClick={() => copyToClipboard(`${proxy.ip}:${proxy.port}`)} className="text-gray-400 hover:text-black dark:hover:text-white transition-colors" title="Copy IP:Port">
                                        <Copy size={12} />
                                    </button>
                                </div>
                                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1 flex items-center gap-1">
                                    <span className="bg-gray-100 dark:bg-[#3f3f46] px-1.5 py-0.5 rounded text-[10px]">{item.proxy_type}</span>
                                    <span title="Credentials">{proxy.login}:******</span>
                                    <button onClick={() => copyToClipboard(
                                      item.proxy_type === 'SOCKS5'
                                        ? `${proxy.ip}:${proxy.port}:${proxy.login}:${proxy.password}`
                                        : `${proxy.ip}:${proxy.login}:${proxy.password}:${item.state || ''}:${item.city || ''}:${item.zip || ''}`
                                    )} className="text-gray-400 hover:text-black dark:hover:text-white transition-colors" title="Copy Full String">
                                        <Copy size={10} />
                                    </button>
                                </div>
                              </div>
                            ) : (
                              <div className="text-sm text-gray-500 dark:text-gray-400 italic">No proxy data</div>
                            )}
                        </td>
                        <td className="px-6 py-4">
                            <span className="font-medium">{item.country}</span>
                            {item.state && <span className="text-xs text-gray-500 dark:text-gray-400 ml-1">/ {item.state}</span>}
                        </td>
                        <td className="px-6 py-4">
                             <div className="flex items-center gap-1.5 text-xs">
                                {item.proxy_type === 'SOCKS5' && <Shield size={14} />}
                                {item.proxy_type === 'PPTP' && <Server size={14} />}
                                {item.proxy_type}
                             </div>
                        </td>
                        <td className="px-6 py-4">
                            <div className="flex flex-col text-xs">
                                <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                                  <Calendar size={10} /> Purchased: {new Date(item.datestamp).toLocaleDateString()}
                                </span>
                                <span className={`flex items-center gap-1 mt-0.5 ${expired ? 'text-red-500' : 'text-green-600 dark:text-green-400'}`}>
                                    <Clock size={10} /> Expires: {new Date(item.expires_at).toLocaleDateString()}
                                </span>
                            </div>
                        </td>
                        <td className="px-6 py-4">
                            {!expired ? (
                                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                                    <CheckCircle2 size={12} /> Active
                                </span>
                            ) : (
                                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                                    <XCircle size={12} /> Expired
                                </span>
                            )}
                        </td>
                        <td className="px-6 py-4 text-right">
                            {!item.isRefunded && hasProxies && proxy ? (
                              <button 
                                onClick={() => setExtendModal({
                                  proxyId: item.id,
                                  proxyType: item.proxy_type,
                                  currentExpiry: item.expires_at,
                                  ip: proxy.ip,
                                  port: proxy.port
                                })}
                                className={`text-xs font-medium ${!expired ? 'text-black dark:text-white' : 'text-blue-600 dark:text-blue-400'} hover:underline`}
                              >
                                {!expired ? 'Extend' : 'Renew'}
                              </button>
                            ) : item.isRefunded ? (
                              <span className="text-xs text-gray-400">Refunded</span>
                            ) : (
                              <span className="text-xs text-gray-400">N/A</span>
                            )}
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
                      {purchases.length === 0 ? 'No purchases found.' : 'No history found matching your filters.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="px-6 py-4 border-t border-gray-200 dark:border-[#27272a] bg-gray-50 dark:bg-[#18181b] flex justify-between items-center transition-colors">
              <span className="text-xs text-gray-500 dark:text-gray-400">
                Showing {filteredData.length} records
              </span>
          </div>
        </div>
      )}

      {/* Extend/Renew Modal */}
      {extendModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white dark:bg-[#18181b] w-full max-w-md rounded-2xl shadow-2xl border border-gray-200 dark:border-[#27272a] overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 dark:border-[#27272a] flex items-center justify-between">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <Clock size={20} /> Extend Proxy
              </h3>
              <button 
                onClick={() => {
                  setExtendModal(null);
                  setExtendError(null);
                  setExtendSuccess(null);
                  setExtendHours(24);
                }} 
                className="text-gray-400 hover:text-gray-900 dark:hover:text-white"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6">
              {/* Proxy Details */}
              <div className="mb-4 p-3 bg-gray-50 dark:bg-[#27272a] rounded-lg">
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Proxy</div>
                <div className="font-mono text-sm font-bold text-gray-900 dark:text-white">
                  {extendModal.ip && extendModal.port ? `${extendModal.ip}:${extendModal.port}` : 'Proxy details unavailable'}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                  Current Expiry: {new Date(extendModal.currentExpiry).toLocaleString()}
                </div>
              </div>

              {/* Hours Input */}
              <div className="mb-4">
                <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-2">
                  Extension Hours
                </label>
                <input 
                  type="number"
                  min="1"
                  max="168"
                  value={extendHours}
                  onChange={(e) => setExtendHours(parseInt(e.target.value) || 1)}
                  className="w-full px-4 py-3 bg-gray-50 dark:bg-[#27272a] border border-gray-200 dark:border-[#3f3f46] rounded-lg focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white text-gray-900 dark:text-white font-medium"
                  placeholder="24"
                />
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Min: 1 hour, Max: 168 hours (7 days)
                </div>
              </div>

              {/* Error/Success Messages */}
              {extendError && (
                <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400 text-sm">
                  {extendError}
                </div>
              )}
              
              {extendSuccess && (
                <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg text-green-700 dark:text-green-400 text-sm">
                  {extendSuccess}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setExtendModal(null);
                    setExtendError(null);
                    setExtendSuccess(null);
                    setExtendHours(24);
                  }}
                  className="flex-1 py-3 bg-gray-100 dark:bg-[#27272a] text-gray-700 dark:text-gray-300 rounded-lg font-bold hover:opacity-80 transition-opacity"
                  disabled={isExtending}
                >
                  Cancel
                </button>
                <button
                  onClick={handleExtendProxy}
                  disabled={isExtending || extendHours < 1 || extendHours > 168}
                  className="flex-1 py-3 bg-black dark:bg-white text-white dark:text-black rounded-lg font-bold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
                >
                  {isExtending ? 'Processing...' : `Extend ${extendHours}h`}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default History;
