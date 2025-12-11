import React, { useState, useEffect } from 'react';
import { Search, Plus, Trash2, Calendar, Hash, Tag } from 'lucide-react';
import { Language, AdminCouponListItem, AdminCouponListResponse } from '../types';
import { TRANSLATIONS } from '../constants';
import { adminApiClient } from '../lib/api-client';

interface CouponsProps {
  lang: Language;
}

const Coupons: React.FC<CouponsProps> = ({ lang }) => {
  const t = TRANSLATIONS[lang];
  const [coupons, setCoupons] = useState<AdminCouponListItem[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [newCode, setNewCode] = useState('');
  const [newDiscount, setNewDiscount] = useState('');
  const [newMaxUses, setNewMaxUses] = useState('');
  const [newExpiry, setNewExpiry] = useState('');

  // Fetch coupons from API
  useEffect(() => {
    const fetchCoupons = async () => {
      try {
        setLoading(true);
        setError(null);

        const response: AdminCouponListResponse = await adminApiClient.getCoupons({
          search: searchTerm || undefined,
          page: 1,
          page_size: 100,
        });

        setCoupons(response.coupons);
      } catch (err: any) {
        console.error('Error fetching coupons:', err);
        setError(err.response?.data?.detail || 'Failed to load coupons');
      } finally {
        setLoading(false);
      }
    };

    const timeoutId = setTimeout(fetchCoupons, 300);
    return () => clearTimeout(timeoutId);
  }, [searchTerm]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const newCoupon = await adminApiClient.createCoupon({
        code: newCode.toUpperCase(),
        discount_percent: Number(newDiscount),
        max_uses: Number(newMaxUses),
        expires_at: newExpiry || undefined,
        is_active: true,
      });

      setCoupons([newCoupon, ...coupons]);
      setIsModalOpen(false);

      // Reset form
      setNewCode('');
      setNewDiscount('');
      setNewMaxUses('');
      setNewExpiry('');
    } catch (err: any) {
      console.error('Error creating coupon:', err);
      alert(err.response?.data?.detail || 'Failed to create coupon');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this coupon?')) return;

    try {
      await adminApiClient.deleteCoupon(id);
      setCoupons(coupons.filter(c => c.id !== id));
    } catch (err: any) {
      console.error('Error deleting coupon:', err);
      alert(err.response?.data?.detail || 'Failed to delete coupon');
    }
  };

  return (
    <div className="space-y-6 relative">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{t.coupons}</h2>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Create and manage promo codes</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 text-sm font-medium transition-colors shadow-sm shadow-blue-500/30"
        >
          <Plus size={16} />
          {t.createCoupon}
        </button>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="p-4 border-b border-gray-100 dark:border-gray-700">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input 
              type="text" 
              placeholder={t.searchCoupon}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white text-sm"
            />
          </div>
        </div>
        
        <div className="overflow-x-auto">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          )}

          {error && (
            <div className="text-center py-12">
              <p className="text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}

          {!loading && !error && (
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 dark:bg-gray-900/50 text-gray-500 dark:text-gray-400 font-medium border-b border-gray-100 dark:border-gray-700">
                <tr>
                  <th className="px-6 py-4">{t.code}</th>
                  <th className="px-6 py-4">{t.discount}</th>
                  <th className="px-6 py-4">{t.used}</th>
                  <th className="px-6 py-4">{t.maxUses}</th>
                  <th className="px-6 py-4">{t.created}</th>
                  <th className="px-6 py-4">{t.expiry}</th>
                  <th className="px-6 py-4">{t.status}</th>
                  <th className="px-6 py-4 text-right">{t.actions}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {coupons.map((coupon) => {
                  const discount = typeof coupon.discount_percent === 'number' ? coupon.discount_percent : parseFloat(coupon.discount_percent.toString());
                  return (
                    <tr key={coupon.id} className="hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
                      <td className="px-6 py-4 font-mono font-bold text-gray-900 dark:text-white">{coupon.code}</td>
                      <td className="px-6 py-4 text-green-600 font-medium">{discount}%</td>
                      <td className="px-6 py-4 text-gray-600 dark:text-gray-300">{coupon.used_count}</td>
                      <td className="px-6 py-4 text-gray-600 dark:text-gray-300">{coupon.max_uses}</td>
                      <td className="px-6 py-4 text-gray-500 dark:text-gray-400">
                        {new Date(coupon.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </td>
                      <td className="px-6 py-4 text-gray-500 dark:text-gray-400 flex items-center gap-2">
                        <Calendar size={14} />
                        {coupon.expires_at ? new Date(coupon.expires_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Unlimited'}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${coupon.is_active ? 'bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-300 dark:border-green-900/50' : 'bg-gray-100 text-gray-600 border-gray-200 dark:bg-gray-700 dark:text-gray-400 dark:border-gray-600'}`}>
                          {coupon.is_active ? t.active : t.expired}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button onClick={() => handleDelete(coupon.id)} className="text-gray-400 hover:text-red-600 transition-colors">
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {coupons.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                      {t.noData}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">{t.modalCreateCoupon}</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">✕</button>
            </div>
            <form onSubmit={handleCreate} className="p-6 space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-500 dark:text-gray-400">{t.inputCode}</label>
                <div className="relative">
                  <Hash className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input required type="text" value={newCode} onChange={e => setNewCode(e.target.value)} className="w-full pl-9 pr-4 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none dark:text-white text-sm" placeholder="SUMMER2025" />
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-500 dark:text-gray-400">{t.inputDiscount}</label>
                <div className="relative">
                  <Tag className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input required type="number" min="1" max="100" value={newDiscount} onChange={e => setNewDiscount(e.target.value)} className="w-full pl-9 pr-4 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none dark:text-white text-sm" placeholder="10" />
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-500 dark:text-gray-400">{t.inputMaxUses}</label>
                <input required type="number" min="1" value={newMaxUses} onChange={e => setNewMaxUses(e.target.value)} className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none dark:text-white text-sm" placeholder="100" />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-500 dark:text-gray-400">{t.inputDate}</label>
                <input type="date" value={newExpiry} onChange={e => setNewExpiry(e.target.value)} className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none dark:text-white text-sm" />
              </div>
              <div className="pt-4 flex gap-3">
                <button type="button" onClick={() => setIsModalOpen(false)} className="flex-1 px-4 py-2 border border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-700">{t.cancel}</button>
                <button type="submit" className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium shadow-lg shadow-blue-500/30">{t.save}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Coupons;
