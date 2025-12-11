import React, { useState, useEffect } from 'react';
import { Search, Wallet, Ban, ShieldCheck, Globe, Smartphone, ChevronLeft, ChevronRight } from 'lucide-react';
import { Language, AdminUserListItem, AdminUserListResponse } from '../types';
import { TRANSLATIONS } from '../constants';
import { adminApiClient } from '../lib/api-client';

interface UsersProps {
  lang: Language;
}

const Users: React.FC<UsersProps> = ({ lang }) => {
  const t = TRANSLATIONS[lang];
  const [searchTerm, setSearchTerm] = useState('');
  const [users, setUsers] = useState<AdminUserListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalUsers, setTotalUsers] = useState(0);
  const pageSize = 50;

  // Balance modal state
  const [balanceModalOpen, setBalanceModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<AdminUserListItem | null>(null);
  const [newBalance, setNewBalance] = useState('');

  // Fetch users from API
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        setLoading(true);
        setError(null);

        const response: AdminUserListResponse = await adminApiClient.getUsers({
          search: searchTerm || undefined,
          page: currentPage,
          page_size: pageSize,
        });

        setUsers(response.users);
        setTotalUsers(response.total);
      } catch (err: any) {
        console.error('Error fetching users:', err);
        setError(err.response?.data?.detail || 'Failed to load users');
      } finally {
        setLoading(false);
      }
    };

    // Debounce search
    const timeoutId = setTimeout(fetchUsers, 300);
    return () => clearTimeout(timeoutId);
  }, [searchTerm, currentPage]);

  const toggleUserStatus = async (userId: number, currentStatus: boolean) => {
    try {
      const blocked_reason = !currentStatus ? 'Blocked by admin' : undefined;
      await adminApiClient.updateUser(userId, {
        is_blocked: !currentStatus,
        blocked_reason,
      });

      // Update local state
      setUsers(users.map(user =>
        user.user_id === userId
          ? { ...user, is_blocked: !currentStatus }
          : user
      ));
    } catch (err: any) {
      console.error('Error updating user:', err);
      alert(err.response?.data?.detail || 'Failed to update user status');
    }
  };

  const handleBalanceUpdate = async () => {
    if (!selectedUser) return;
    try {
      await adminApiClient.updateUser(selectedUser.user_id, {
        balance: parseFloat(newBalance)
      });
      // Update local state
      setUsers(users.map(user =>
        user.user_id === selectedUser.user_id
          ? { ...user, balance: parseFloat(newBalance) }
          : user
      ));
      setBalanceModalOpen(false);
      setSelectedUser(null);
      setNewBalance('');
    } catch (err: any) {
      console.error('Error updating balance:', err);
      alert(err.response?.data?.detail || 'Failed to update balance');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{t.users}</h2>
        <p className="text-gray-500 dark:text-gray-400 mt-1">{t.registered}</p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="p-4 border-b border-gray-100 dark:border-gray-700">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder={t.searchPlaceholder}
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
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
                  <th className="px-6 py-4">ID</th>
                  <th className="px-6 py-4">Access Code</th>
                  <th className="px-6 py-4">Username</th>
                  <th className="px-6 py-4">{t.platform}</th>
                  <th className="px-6 py-4">{t.balance}</th>
                  <th className="px-6 py-4">{t.spent}</th>
                  <th className="px-6 py-4">{t.purchases}</th>
                  <th className="px-6 py-4">{t.registration}</th>
                  <th className="px-6 py-4">{t.status}</th>
                  <th className="px-6 py-4">{t.actions}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {users.map((user) => {
                  const balance = typeof user.balance === 'number' ? user.balance : parseFloat(user.balance.toString());
                  const spent = typeof user.total_spent === 'number' ? user.total_spent : parseFloat(user.total_spent.toString());
                  return (
                    <tr key={user.user_id} className="hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
                      <td className="px-6 py-4 text-gray-500 dark:text-gray-400">{user.user_id}</td>
                      <td className="px-6 py-4">
                        <span className="font-mono text-xs text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-900/50 px-2 py-1 rounded">
                          {user.access_code}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-medium text-gray-900 dark:text-white">{user.username || '—'}</td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${user.platform_registered === 'telegram' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' : 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'}`}>
                          {user.platform_registered === 'telegram' ? <Smartphone size={12} /> : <Globe size={12} />}
                          {user.platform_registered}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-green-600 font-medium">${balance.toFixed(2)}</td>
                      <td className="px-6 py-4 text-gray-500 dark:text-gray-400">${spent.toFixed(2)}</td>
                      <td className="px-6 py-4 text-gray-900 dark:text-white">{user.purchases_count}</td>
                      <td className="px-6 py-4 text-gray-500 dark:text-gray-400">
                        {new Date(user.datestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${!user.is_blocked ? 'bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-300 dark:border-green-900/50' : 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-300 dark:border-red-900/50'}`}>
                          {!user.is_blocked ? t.active : t.blocked}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <button
                            onClick={() => {
                              setSelectedUser(user);
                              setNewBalance(balance.toFixed(2));
                              setBalanceModalOpen(true);
                            }}
                            className="text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 flex items-center gap-1 text-xs font-medium transition-colors"
                          >
                            <Wallet size={14} /> {t.balance}
                          </button>
                          <button
                            onClick={() => toggleUserStatus(user.user_id, user.is_blocked)}
                            className={`flex items-center gap-1 text-xs font-medium transition-colors ${!user.is_blocked ? 'text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400' : 'text-green-600 hover:text-green-700 dark:text-green-400'}`}
                          >
                            {!user.is_blocked ? <Ban size={14} /> : <ShieldCheck size={14} />}
                            {!user.is_blocked ? t.ban : t.unban}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
                {users.length === 0 && (
                  <tr>
                    <td colSpan={10} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                      {t.noData}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        {!loading && !error && totalUsers > pageSize && (
          <div className="px-6 py-4 border-t border-gray-100 dark:border-gray-700 flex items-center justify-between">
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {t.showing || 'Показано'} {((currentPage - 1) * pageSize) + 1}–{Math.min(currentPage * pageSize, totalUsers)} {t.of || 'из'} {totalUsers}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-2 rounded-lg border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-750 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft size={18} />
              </button>

              {/* Page numbers */}
              {(() => {
                const totalPages = Math.ceil(totalUsers / pageSize);
                const pages: (number | string)[] = [];

                if (totalPages <= 7) {
                  for (let i = 1; i <= totalPages; i++) pages.push(i);
                } else {
                  pages.push(1);
                  if (currentPage > 3) pages.push('...');

                  const start = Math.max(2, currentPage - 1);
                  const end = Math.min(totalPages - 1, currentPage + 1);

                  for (let i = start; i <= end; i++) pages.push(i);

                  if (currentPage < totalPages - 2) pages.push('...');
                  pages.push(totalPages);
                }

                return pages.map((page, idx) => (
                  typeof page === 'number' ? (
                    <button
                      key={idx}
                      onClick={() => setCurrentPage(page)}
                      className={`min-w-[36px] h-9 px-3 rounded-lg text-sm font-medium transition-colors ${
                        currentPage === page
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-750'
                      }`}
                    >
                      {page}
                    </button>
                  ) : (
                    <span key={idx} className="px-2 text-gray-400">...</span>
                  )
                ));
              })()}

              <button
                onClick={() => setCurrentPage(p => Math.min(Math.ceil(totalUsers / pageSize), p + 1))}
                disabled={currentPage >= Math.ceil(totalUsers / pageSize)}
                className="p-2 rounded-lg border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-750 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Balance Modal */}
      {balanceModalOpen && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              {t.balance}: {selectedUser.username || `User #${selectedUser.user_id}`}
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t.newBalance || 'New Balance'} ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={newBalance}
                  onChange={(e) => setNewBalance(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
                  placeholder="0.00"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => {
                    setBalanceModalOpen(false);
                    setSelectedUser(null);
                    setNewBalance('');
                  }}
                  className="flex-1 px-4 py-2 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
                >
                  {t.cancel || 'Cancel'}
                </button>
                <button
                  onClick={handleBalanceUpdate}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  {t.save || 'Save'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Users;
