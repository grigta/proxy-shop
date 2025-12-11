import React, { useState, useRef, useEffect } from 'react';
import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { 
  LayoutGrid, 
  HelpCircle, 
  Headset,
  Sun,
  Moon,
  LogOut,
  CreditCard,
  Clock,
  X,
  Plus,
  DollarSign,
  Wallet,
  Network,
  History,
  Globe,
  Key,
  Eye,
  EyeOff,
  Copy,
  Check,
  ExternalLink,
  RefreshCcw
} from 'lucide-react';
import { AxiosError } from 'axios';
import { useTheme } from '../ThemeContext';
import { useAuth } from '../AuthContext';
import { apiClient } from '../lib/api-client';
import { MIN_DEPOSIT_USD } from '../lib/constants';
import { copyToClipboard as copyText } from '../lib/clipboard';
import type { CreatePaymentResponse, TransactionHistoryItem, APIError } from '../types/api';

export const Layout: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const { user, logout, updateUser } = useAuth();
  
  // State for User/Wallet
  const [language, setLanguage] = useState<'en' | 'ru'>('en');
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [activeModal, setActiveModal] = useState<'none' | 'deposit' | 'history'>('none');
  const [depositAmount, setDepositAmount] = useState<string>('');
  const [transactions, setTransactions] = useState<TransactionHistoryItem[]>([]);
  
  // Payment states
  const [paymentInvoice, setPaymentInvoice] = useState<CreatePaymentResponse | null>(null);
  const [isCreatingPayment, setIsCreatingPayment] = useState(false);
  const [isLoadingTransactions, setIsLoadingTransactions] = useState(false);
  const [paymentError, setPaymentError] = useState<string | null>(null);
  const [hasLoadedTransactions, setHasLoadedTransactions] = useState(false);

  // Access Key visibility state
  const [isKeyVisible, setIsKeyVisible] = useState(false);
  const [isKeyCopied, setIsKeyCopied] = useState(false);
  
  // Referral links copy states
  const [isBotLinkCopied, setIsBotLinkCopied] = useState(false);
  const [isWebLinkCopied, setIsWebLinkCopied] = useState(false);
  
  // TxID copy state
  const [copiedTxId, setCopiedTxId] = useState<string | null>(null);

  const menuRef = useRef<HTMLDivElement>(null);

  // Fetch user profile on mount and when user changes
  useEffect(() => {
    const fetchUserProfile = async () => {
      if (!user) return;
      
      try {
        const profile = await apiClient.getProfile();
        updateUser(profile);
      } catch (err) {
        console.error('Failed to fetch user profile:', err);
        // Silently fail - user is already authenticated
      }
    };

    fetchUserProfile();
  }, [user, updateUser]); // Depend on user and updateUser

  // Fetch transaction history when history modal opens
  useEffect(() => {
    const fetchTransactionHistory = async () => {
      if (activeModal !== 'history' || !user) return;
      
      setIsLoadingTransactions(true);
      try {
        const response = await apiClient.getPaymentHistory(user.user_id, { page: 1, page_size: 20 });
        setTransactions(response.transactions);
        setHasLoadedTransactions(true);
      } catch (err) {
        console.error('Failed to fetch transaction history:', err);
        // Silently fail - user can retry by closing and reopening modal
      } finally {
        setIsLoadingTransactions(false);
      }
    };

    fetchTransactionHistory();
  }, [activeModal, user]);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsProfileOpen(false);
        setIsKeyVisible(false); // Reset key visibility when menu closes
        setIsKeyCopied(false);
        setIsBotLinkCopied(false);
        setIsWebLinkCopied(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  // Format helper
  const formatAccessCode = (code: string) => {
    return code.replace(/(\d{3})(\d{3})(\d{3})/, '$1-$2-$3');
  };

  const copyAccessKey = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (user?.access_code) {
      // Copy the formatted code for better UX
      const success = await copyText(formatAccessCode(user.access_code));
      if (success) {
        setIsKeyCopied(true);
        setTimeout(() => setIsKeyCopied(false), 2000);
      }
    }
  };

  const copyReferralLink = async (link: string, type: 'bot' | 'web') => {
    const success = await copyText(link);
    if (success) {
      if (type === 'bot') {
        setIsBotLinkCopied(true);
        setTimeout(() => setIsBotLinkCopied(false), 2000);
      } else {
        setIsWebLinkCopied(true);
        setTimeout(() => setIsWebLinkCopied(false), 2000);
      }
    }
  };

  // Map title based on path
  const getPageTitle = () => {
    switch (location.pathname) {
      case '/socks': return 'SOCKS5 Proxies';
      case '/pptp': return 'PPTP VPN';
      case '/history': return 'Proxy History';
      case '/faq': return 'FAQ';
      default: return 'Overview';
    }
  };

  const navItems = [
    { icon: LayoutGrid, path: '/socks', label: 'SOCKS5' },
    { icon: Network, path: '/pptp', label: 'PPTP' },
    { icon: History, path: '/history', label: 'History' },
    { icon: HelpCircle, path: '/faq', label: 'FAQ' }, 
    { icon: Headset, path: '/support', label: 'Support (Mock)' }, 
  ];

  const handleCreatePayment = async () => {
    setPaymentError(null);
    
    // Validation: handle empty amount vs invalid format vs below minimum
    if (depositAmount) {
      const amount = parseFloat(depositAmount);
      
      // Check for invalid format (NaN)
      if (isNaN(amount)) {
        setPaymentError('Please enter a valid amount');
        return;
      }
      
      // Check minimum amount
      if (amount < MIN_DEPOSIT_USD) {
        setPaymentError(`Minimum deposit amount is $${MIN_DEPOSIT_USD}`);
        return;
      }
    }

    setIsCreatingPayment(true);

    try {
      // Pass undefined if depositAmount is empty to use backend default
      const response = await apiClient.generateAddress({ 
        amount_usd: depositAmount ? depositAmount : undefined 
      });
      setPaymentInvoice(response);
      // Don't close modal - show payment details
    } catch (err) {
      const axiosError = err as AxiosError<APIError>;
      const errorMessage = axiosError.response?.data.detail || 'Failed to create payment. Please try again.';
      setPaymentError(errorMessage);
      console.error('Payment creation failed:', err);
    } finally {
      setIsCreatingPayment(false);
    }
  };

  const handleOpenPaymentLink = () => {
    if (paymentInvoice?.payment_url) {
      window.open(paymentInvoice.payment_url, '_blank', 'noopener,noreferrer');
    }
  };

  const handleCheckBalance = async () => {
    try {
      const profile = await apiClient.getProfile();
      updateUser(profile);
      // Optionally show success feedback here
    } catch (err) {
      console.error('Failed to refresh balance:', err);
      // Silently fail - user can retry
    }
  };

  const handleCreateNewPayment = () => {
    setPaymentInvoice(null);
    setDepositAmount('');
    setPaymentError(null);
    // Keep modal open for creating another payment
  };

  const handleCloseDepositModal = () => {
    setActiveModal('none');
    setPaymentInvoice(null);
    setDepositAmount('');
    setPaymentError(null);
  };

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-[#09090b] overflow-hidden transition-colors duration-200">
      {/* Sidebar */}
      <aside className="w-16 bg-white dark:bg-[#18181b] border-r border-gray-200 dark:border-[#27272a] flex flex-col items-center py-6 z-20 flex-shrink-0 transition-colors duration-200">
        <div className="mb-8 cursor-pointer" onClick={() => navigate('/')}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-black dark:text-white transition-colors">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>

        <nav className="flex-1 flex flex-col gap-6 w-full items-center">
          {navItems.map((item, idx) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <NavLink
                key={idx}
                to={item.path}
                className={`p-2 rounded-lg transition-colors duration-200 hover:bg-gray-100 dark:hover:bg-[#27272a] relative group ${
                  isActive 
                    ? 'text-black dark:text-white bg-gray-100 dark:bg-[#27272a]' 
                    : 'text-gray-400 dark:text-gray-500'
                }`}
              >
                <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
                <div className="absolute left-14 bg-black dark:bg-white text-white dark:text-black text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
                  {item.label}
                </div>
              </NavLink>
            );
          })}
        </nav>

        <div className="mt-auto pb-4">
           <button onClick={handleLogout} className="p-2 text-gray-400 dark:text-gray-500 hover:text-black dark:hover:text-white transition-colors">
            <LogOut size={20} />
           </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden relative">
        {/* Top Header */}
        <header className="h-16 bg-white dark:bg-[#18181b] border-b border-gray-200 dark:border-[#27272a] flex items-center justify-between px-8 flex-shrink-0 transition-colors duration-200">
          <h1 className="text-xl font-bold text-gray-900 dark:text-white transition-colors">{getPageTitle()}</h1>
          
          <div className="flex items-center gap-4">
            <button onClick={toggleTheme} className="p-2 text-gray-500 hover:text-black dark:text-gray-400 dark:hover:text-white transition-colors">
              {theme === 'dark' ? <Moon size={18} /> : <Sun size={18} />}
            </button>
            
            <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 dark:bg-[#27272a] rounded-lg border border-gray-200 dark:border-[#3f3f46]">
               <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">Balance</span>
               <span className="text-sm font-bold text-gray-900 dark:text-white">${parseFloat(user?.balance || '0').toFixed(2)}</span>
               <button onClick={() => setActiveModal('deposit')} className="ml-2 p-0.5 bg-black dark:bg-white text-white dark:text-black rounded hover:opacity-80 transition-opacity">
                  <Plus size={12} />
               </button>
            </div>

            {/* User Menu */}
            <div className="relative" ref={menuRef}>
              <button 
                onClick={() => setIsProfileOpen(!isProfileOpen)}
                className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden border border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white transition-all"
              >
                <img src="https://picsum.photos/seed/user/200/200" alt="User" className="w-full h-full object-cover" />
              </button>

              {isProfileOpen && (
                <div className="absolute right-0 top-full mt-2 w-72 bg-white dark:bg-[#18181b] rounded-xl shadow-xl border border-gray-200 dark:border-[#27272a] z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-100">
                  
                  {/* Access Key Section */}
                  <div className="p-4 border-b border-gray-100 dark:border-[#27272a] bg-gray-50 dark:bg-[#27272a]/50">
                    <div className="flex items-center justify-between mb-2">
                        <p className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase">My Access Key</p>
                        <button onClick={() => setIsKeyVisible(!isKeyVisible)} className="text-gray-400 hover:text-black dark:hover:text-white">
                            {isKeyVisible ? <EyeOff size={14} /> : <Eye size={14} />}
                        </button>
                    </div>
                    <div
                        onClick={() => setIsKeyVisible(!isKeyVisible)}
                        className="bg-white dark:bg-[#18181b] border border-gray-200 dark:border-[#3f3f46] rounded-lg p-2 flex items-center justify-between cursor-pointer group"
                    >
                        <div className={`font-mono text-sm font-bold text-black dark:text-white transition-all tracking-widest ${isKeyVisible ? '' : 'blur-sm select-none'}`}>
                            {user?.access_code ? formatAccessCode(user.access_code) : "XXX-XXX-XXX"}
                        </div>
                        {isKeyVisible && (
                            <button onClick={copyAccessKey} className="text-gray-400 hover:text-black dark:hover:text-white p-1 rounded">
                                {isKeyCopied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
                            </button>
                        )}
                    </div>
                  </div>
                  
                  {/* Referral Links Section */}
                  {user?.referral_link_bot && user?.referral_link_web && (
                    <div className="p-4 border-b border-gray-100 dark:border-[#27272a] bg-gray-50 dark:bg-[#27272a]/50">
                      <p className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase mb-2">Referral Links</p>
                      
                      {/* Bot Link */}
                      <div className="mb-2">
                        <div className="text-[10px] text-gray-500 dark:text-gray-400 mb-1">Telegram Bot</div>
                        <div className="bg-white dark:bg-[#18181b] border border-gray-200 dark:border-[#3f3f46] rounded-lg p-2 flex items-center justify-between">
                          <div className="text-xs text-gray-900 dark:text-white truncate flex-1 mr-2">
                            {user.referral_link_bot}
                          </div>
                          <button 
                            onClick={() => copyReferralLink(user.referral_link_bot, 'bot')} 
                            className="text-gray-400 hover:text-black dark:hover:text-white p-1 rounded flex-shrink-0"
                          >
                            {isBotLinkCopied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
                          </button>
                        </div>
                      </div>
                      
                      {/* Web Link */}
                      <div>
                        <div className="text-[10px] text-gray-500 dark:text-gray-400 mb-1">Web Interface</div>
                        <div className="bg-white dark:bg-[#18181b] border border-gray-200 dark:border-[#3f3f46] rounded-lg p-2 flex items-center justify-between">
                          <div className="text-xs text-gray-900 dark:text-white truncate flex-1 mr-2">
                            {user.referral_link_web}
                          </div>
                          <button 
                            onClick={() => copyReferralLink(user.referral_link_web, 'web')} 
                            className="text-gray-400 hover:text-black dark:hover:text-white p-1 rounded flex-shrink-0"
                          >
                            {isWebLinkCopied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  <div className="p-2">
                    <button 
                      onClick={() => { setActiveModal('deposit'); setIsProfileOpen(false); }}
                      className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-[#27272a] rounded-lg flex items-center gap-3 transition-colors"
                    >
                      <div className="p-1.5 bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 rounded-md">
                        <Wallet size={16} />
                      </div>
                      <div>
                        <span className="block font-medium">Deposit Funds</span>
                        <span className="block text-[10px] text-gray-400">Add money to your balance</span>
                      </div>
                    </button>

                    <button 
                      onClick={() => { setActiveModal('history'); setIsProfileOpen(false); }}
                      className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-[#27272a] rounded-lg flex items-center gap-3 transition-colors mt-1"
                    >
                      <div className="p-1.5 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-md">
                        <Clock size={16} />
                      </div>
                      <div>
                        <span className="block font-medium">Purchase History</span>
                        <span className="block text-[10px] text-gray-400">View transactions</span>
                      </div>
                    </button>
                  </div>

                  <div className="p-2 border-t border-gray-100 dark:border-[#27272a]">
                    <button 
                      onClick={() => setLanguage(language === 'en' ? 'ru' : 'en')}
                      className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-[#27272a] rounded-lg flex items-center justify-between transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-1.5 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-md">
                          <Globe size={16} />
                        </div>
                        <span className="font-medium">Language</span>
                      </div>
                      <span className="text-xs font-medium text-gray-500 dark:text-gray-400">{language === 'en' ? 'English' : 'Русский'}</span>
                    </button>
                  </div>

                  <div className="p-2 border-t border-gray-100 dark:border-[#27272a]">
                    <button 
                      onClick={handleLogout}
                      className="w-full text-left px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/10 rounded-lg flex items-center gap-2 transition-colors"
                    >
                      <LogOut size={16} />
                      Sign Out
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-y-auto p-0">
          <Outlet />
        </div>

        {/* MODALS */}
        
        {/* Deposit Modal */}
        {activeModal === 'deposit' && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-white dark:bg-[#18181b] w-full max-w-md rounded-2xl shadow-2xl border border-gray-200 dark:border-[#27272a] overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100 dark:border-[#27272a] flex items-center justify-between">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <CreditCard size={20} /> {paymentInvoice ? 'Payment Details' : 'Add Funds'}
                </h3>
                <button onClick={handleCloseDepositModal} className="text-gray-400 hover:text-gray-900 dark:hover:text-white">
                  <X size={20} />
                </button>
              </div>
              
              <div className="p-6">
                {!paymentInvoice ? (
                  // Stage 1: Amount Input
                  <>
                    <div className="mb-6">
                      <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-2">Select Amount</label>
                      <div className="grid grid-cols-3 gap-3 mb-4">
                        {[50, 100, 200].map(amt => (
                          <button 
                            key={amt}
                            onClick={() => setDepositAmount(amt.toString())}
                            className={`py-2 rounded-lg border text-sm font-semibold transition-all ${
                              depositAmount === amt.toString()
                                ? 'border-black dark:border-white bg-black dark:bg-white text-white dark:text-black'
                                : 'border-gray-200 dark:border-[#3f3f46] text-gray-700 dark:text-gray-300 hover:border-gray-400 dark:hover:border-gray-500'
                            }`}
                          >
                            ${amt}
                          </button>
                        ))}
                      </div>
                      <div className="relative">
                        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">
                          <DollarSign size={16} />
                        </div>
                        <input 
                          type="number" 
                          value={depositAmount}
                          onChange={(e) => setDepositAmount(e.target.value)}
                          placeholder="Custom amount"
                          className="w-full pl-9 pr-4 py-3 bg-gray-50 dark:bg-[#27272a] border border-gray-200 dark:border-[#3f3f46] rounded-lg focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white text-gray-900 dark:text-white font-medium"
                        />
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                        Minimum deposit: ${MIN_DEPOSIT_USD}
                      </p>
                      {paymentError && (
                        <p className="text-xs text-red-600 dark:text-red-400 mt-2">
                          {paymentError}
                        </p>
                      )}
                    </div>

                    <button 
                      onClick={handleCreatePayment}
                      disabled={!depositAmount || isCreatingPayment}
                      className="w-full py-3 bg-black dark:bg-white text-white dark:text-black rounded-lg font-bold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity flex items-center justify-center gap-2"
                    >
                      {isCreatingPayment ? 'Creating...' : 'Create Payment'}
                    </button>
                  </>
                ) : (
                  // Stage 2: Payment Details
                  <>
                    <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                      <div className="flex items-start gap-2 mb-3">
                        <span className="text-2xl">✅</span>
                        <div className="flex-1">
                          <h4 className="text-sm font-bold text-green-800 dark:text-green-300 mb-2">
                            Payment Invoice Created
                          </h4>
                          <div className="space-y-1.5 text-xs text-gray-700 dark:text-gray-300">
                            <div className="flex justify-between">
                              <span className="text-gray-500 dark:text-gray-400">Order ID:</span>
                              <span className="font-mono font-semibold">{paymentInvoice.order_id}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500 dark:text-gray-400">Amount:</span>
                              <span className="font-bold">${paymentInvoice.amount_usd}</span>
                            </div>
                            {paymentInvoice.expired_at && (
                              <div className="flex justify-between">
                                <span className="text-gray-500 dark:text-gray-400">Expires:</span>
                                <span className="font-medium">
                                  {new Date(paymentInvoice.expired_at).toLocaleString()}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    <button 
                      onClick={handleOpenPaymentLink}
                      className="w-full py-3 bg-black dark:bg-white text-white dark:text-black rounded-lg font-bold hover:opacity-90 transition-opacity flex items-center justify-center gap-2 mb-3"
                    >
                      <ExternalLink size={18} />
                      Proceed to Payment
                    </button>

                    <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                      <p className="text-xs text-blue-800 dark:text-blue-300 flex items-start gap-2">
                        <span>ℹ️</span>
                        <span>After payment, your balance will be credited automatically. Click "Check Balance" to refresh.</span>
                      </p>
                    </div>

                    <button 
                      onClick={handleCheckBalance}
                      className="w-full py-2.5 bg-gray-100 dark:bg-[#27272a] text-gray-900 dark:text-white rounded-lg font-semibold hover:bg-gray-200 dark:hover:bg-[#3f3f46] transition-colors flex items-center justify-center gap-2 mb-2"
                    >
                      <RefreshCcw size={16} />
                      Check Balance
                    </button>

                    <button 
                      onClick={handleCreateNewPayment}
                      className="w-full py-2.5 border-2 border-gray-300 dark:border-[#3f3f46] text-gray-700 dark:text-gray-300 rounded-lg font-semibold hover:border-gray-400 dark:hover:border-gray-500 transition-colors"
                    >
                      Create Another Payment
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {/* History Modal */}
        {activeModal === 'history' && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-white dark:bg-[#18181b] w-full max-w-4xl rounded-2xl shadow-2xl border border-gray-200 dark:border-[#27272a] overflow-hidden flex flex-col max-h-[80vh]">
              <div className="px-6 py-4 border-b border-gray-100 dark:border-[#27272a] flex items-center justify-between flex-shrink-0">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <Clock size={20} /> Transaction History
                </h3>
                <button onClick={() => setActiveModal('none')} className="text-gray-400 hover:text-gray-900 dark:hover:text-white">
                  <X size={20} />
                </button>
              </div>
              
              <div className="overflow-y-auto p-0">
                {isLoadingTransactions ? (
                  <div className="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
                    <div className="inline-block w-8 h-8 border-4 border-gray-300 dark:border-gray-600 border-t-black dark:border-t-white rounded-full animate-spin mb-3"></div>
                    <p>Loading transactions...</p>
                  </div>
                ) : (
                  <table className="w-full text-left border-collapse">
                    <thead className="bg-gray-50 dark:bg-[#27272a] text-xs uppercase text-gray-500 dark:text-gray-400 sticky top-0">
                      <tr>
                        <th className="px-4 py-3 font-medium">Date</th>
                        <th className="px-4 py-3 font-medium">Chain</th>
                        <th className="px-4 py-3 font-medium">Amount</th>
                        <th className="px-4 py-3 font-medium">USD Value</th>
                        <th className="px-4 py-3 font-medium">TxID</th>
                        <th className="px-4 py-3 font-medium text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-[#27272a]">
                      {transactions.length > 0 ? (
                        transactions.map((tx) => (
                          <tr key={tx.id_tranz} className="hover:bg-gray-50 dark:hover:bg-[#27272a] transition-colors text-sm text-gray-900 dark:text-gray-300">
                            <td className="px-4 py-3 text-gray-500 dark:text-gray-400 whitespace-nowrap">
                              {new Date(tx.dateOfTransaction).toLocaleDateString()}
                            </td>
                            <td className="px-4 py-3">
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">
                                {tx.chain}
                              </span>
                            </td>
                            <td className="px-4 py-3 font-mono text-xs">
                              {parseFloat(tx.coin_amount).toFixed(8)} {tx.currency}
                            </td>
                            <td className="px-4 py-3 font-semibold text-green-600 dark:text-green-400">
                              +${parseFloat(tx.amount_in_dollar).toFixed(2)}
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-xs text-gray-600 dark:text-gray-400">
                                  {tx.txid.length > 16 ? `${tx.txid.slice(0, 8)}...${tx.txid.slice(-8)}` : tx.txid}
                                </span>
                                <button
                                  onClick={async () => {
                                    const success = await copyText(tx.txid);
                                    if (success) {
                                      setCopiedTxId(tx.txid);
                                      setTimeout(() => setCopiedTxId(null), 2000);
                                    }
                                  }}
                                  className="text-gray-400 hover:text-gray-900 dark:hover:text-white p-1"
                                  title="Copy TxID"
                                >
                                  {copiedTxId === tx.txid ? (
                                    <Check size={12} className="text-green-500" />
                                  ) : (
                                    <Copy size={12} />
                                  )}
                                </button>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-center">
                              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                                (tx.confirmation ?? 0) >= 1
                                  ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                              }`}>
                                {tx.confirmation ?? 0} conf
                              </span>
                            </td>
                          </tr>
                        ))
                      ) : (
                        !isLoadingTransactions && hasLoadedTransactions && (
                          <tr>
                            <td colSpan={6} className="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
                              No transactions found.
                            </td>
                          </tr>
                        )
                      )}
                    </tbody>
                  </table>
                )}
              </div>
              <div className="p-4 border-t border-gray-100 dark:border-[#27272a] bg-gray-50 dark:bg-[#27272a] text-center text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
                {isLoadingTransactions ? 'Loading...' : `Showing ${transactions.length} transactions`}
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  );
};

// Helper icons for table
const ArrowUpIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="transform rotate-45"><line x1="12" y1="19" x2="12" y2="5"></line><polyline points="5 12 12 5 19 12"></polyline></svg>
);

const ArrowDownIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="transform rotate-45"><line x1="12" y1="5" x2="12" y2="19"></line><polyline points="19 12 12 19 5 12"></polyline></svg>
);