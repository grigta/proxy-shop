import React, { useState, useEffect } from 'react';
import { Moon, Sun, Menu } from 'lucide-react';
import { View, Language, Theme } from './types';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import Users from './components/Users';
import Coupons from './components/Coupons';
import Proxies from './components/Proxies';
import Broadcast from './components/Broadcast';
import Login from './components/Login';
import { adminApiClient } from './lib/api-client';

const App: React.FC = () => {
  const [view, setView] = useState<View>('dashboard');
  const [theme, setTheme] = useState<Theme>('light');
  const [lang, setLang] = useState<Language>('ru');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      // First check if token exists in localStorage
      const hasToken = adminApiClient.isAuthenticated();
      
      if (!hasToken) {
        setIsAuthenticated(false);
        return;
      }

      // Validate token with backend to ensure it's not expired or invalid
      const isValid = await adminApiClient.validateToken();
      
      if (!isValid) {
        // Token is invalid, clear everything and show login
        setIsAuthenticated(false);
      } else {
        // Token is valid
        setIsAuthenticated(true);
      }
    };
    
    checkAuth();
  }, []);

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    adminApiClient.logout();
    setIsAuthenticated(false);
    setView('dashboard');
  };

  // If not authenticated, show login page
  if (!isAuthenticated) {
    return (
      <Login 
        onLogin={handleLogin}
        lang={lang}
        setLang={setLang}
        theme={theme}
        setTheme={setTheme}
      />
    );
  }

  const renderContent = () => {
    switch (view) {
      case 'dashboard': return <Dashboard lang={lang} />;
      case 'users': return <Users lang={lang} />;
      case 'coupons': return <Coupons lang={lang} />;
      case 'proxies': return <Proxies lang={lang} />;
      case 'broadcast': return <Broadcast lang={lang} />;
      default: return <Dashboard lang={lang} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200 font-sans">
      <Sidebar 
        currentView={view} 
        onChangeView={(v) => { setView(v); setIsMobileMenuOpen(false); }} 
        lang={lang}
        onLogout={handleLogout}
      />
      
      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 w-full z-40 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3 flex justify-between items-center shadow-sm">
         <div className="flex items-center gap-3">
            <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} className="text-gray-600 dark:text-gray-300">
              <Menu size={24} />
            </button>
            <span className="font-bold text-gray-800 dark:text-white">Proxy Shop</span>
         </div>
         <div className="flex gap-2">
             <button 
                onClick={() => setTheme(prev => prev === 'light' ? 'dark' : 'light')}
                className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
              </button>
         </div>
      </div>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
         <div className="fixed inset-0 z-30 bg-black/50 md:hidden" onClick={() => setIsMobileMenuOpen(false)}>
             <div className="bg-white dark:bg-gray-800 h-full w-64 p-4" onClick={e => e.stopPropagation()}>
                <Sidebar 
                  currentView={view} 
                  onChangeView={(v) => { setView(v); setIsMobileMenuOpen(false); }} 
                  lang={lang}
                  onLogout={handleLogout}
                />
             </div>
         </div>
      )}

      <main className="md:ml-64 min-h-screen p-6 pt-20 md:pt-6">
        {/* Desktop Header Tools */}
        <div className="hidden md:flex justify-end mb-6 gap-4 items-center">
          
          {/* Language Toggle Switch */}
          <div className="flex items-center bg-gray-200 dark:bg-gray-700 rounded-full p-1 cursor-pointer w-36 relative h-9 select-none" onClick={() => setLang(prev => prev === 'en' ? 'ru' : 'en')}>
             <div className={`absolute top-1 bottom-1 w-1/2 bg-white dark:bg-gray-600 rounded-full shadow-sm transition-all duration-300 ${lang === 'ru' ? 'right-1' : 'left-1'}`}></div>
             <span className={`z-10 w-1/2 text-center text-xs font-bold transition-colors duration-300 ${lang === 'en' ? 'text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400'}`}>English</span>
             <span className={`z-10 w-1/2 text-center text-xs font-bold transition-colors duration-300 ${lang === 'ru' ? 'text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400'}`}>Русский</span>
          </div>

          {/* Theme Toggle Switch */}
          <div className="flex items-center gap-3 pl-4 border-l border-gray-200 dark:border-gray-700">
            <span className="text-sm text-gray-500 dark:text-gray-400 hidden lg:block">
              {theme === 'light' ? 'Light Mode' : 'Dark Mode'}
            </span>
            <button 
              onClick={() => setTheme(prev => prev === 'light' ? 'dark' : 'light')}
              className={`relative inline-flex h-7 w-14 items-center rounded-full transition-colors duration-300 focus:outline-none ${theme === 'dark' ? 'bg-blue-600' : 'bg-gray-300'}`}
            >
              <span
                className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-md transition-transform duration-300 ${theme === 'dark' ? 'translate-x-8' : 'translate-x-1'} flex items-center justify-center`}
              >
                {theme === 'dark' ? <Moon size={12} className="text-blue-600" /> : <Sun size={12} className="text-yellow-500" />}
              </span>
            </button>
          </div>
        </div>

        <div className="max-w-7xl mx-auto">
          {renderContent()}
        </div>
      </main>
    </div>
  );
};

export default App;