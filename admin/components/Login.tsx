import React, { useState } from 'react';
import { Lock, ArrowRight, AlertCircle, Sun, Moon } from 'lucide-react';
import { Language, Theme } from '../types';
import { TRANSLATIONS } from '../constants';
import { adminApiClient, LoginResponse } from '../lib/api-client';
import { AxiosError } from 'axios';

interface LoginProps {
  onLogin: () => void;
  lang: Language;
  setLang: (lang: Language) => void;
  theme: Theme;
  setTheme: (theme: Theme) => void;
}

const Login: React.FC<LoginProps> = ({ onLogin, lang, setLang, theme, setTheme }) => {
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const t = TRANSLATIONS[lang];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!code.trim()) {
      setError(t.invalidCode);
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response: LoginResponse = await adminApiClient.login(code);
      
      // Strict check: only is_admin === true is accepted
      if (response.is_admin === true) {
        // Successful admin login
        onLogin();
      } else {
        // This should not happen due to validation in api-client, but add as safeguard
        console.error('Unexpected: non-admin response received', response);
        adminApiClient.logout();
        setError(t.accessDenied);
      }
    } catch (err) {
      console.error('Login error:', err);
      
      const axiosError = err as AxiosError<{ detail?: string }>;
      
      // Handle different error scenarios
      if (axiosError.response?.status === 401) {
        setError(t.invalidCode);
      } else if (axiosError.response?.status === 403) {
        setError(t.accessDenied);
      } else if (axiosError.response?.status === 500) {
        // Protocol error
        const errorDetail = axiosError.response?.data?.detail || 'Technical error: invalid API response';
        setError(errorDetail);
      } else {
        setError(t.invalidCode);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Convert to uppercase and set
    const value = e.target.value.toUpperCase();
    setCode(value);
    
    // Clear error when user starts typing
    if (error) {
      setError('');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4 transition-colors duration-200">
      {/* Language and Theme Switchers */}
      <div className="fixed top-4 right-4 flex gap-3 z-50">
        {/* Language Toggle */}
        <div 
          className="flex items-center bg-white dark:bg-gray-800 rounded-full p-1 cursor-pointer shadow-lg transition-colors duration-200"
          onClick={() => setLang(lang === 'en' ? 'ru' : 'en')}
        >
          <div className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-300 ${
            lang === 'en' 
              ? 'bg-blue-600 text-white' 
              : 'text-gray-600 dark:text-gray-400'
          }`}>
            EN
          </div>
          <div className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-300 ${
            lang === 'ru' 
              ? 'bg-blue-600 text-white' 
              : 'text-gray-600 dark:text-gray-400'
          }`}>
            РУ
          </div>
        </div>

        {/* Theme Toggle */}
        <button
          onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
          className="p-2.5 bg-white dark:bg-gray-800 rounded-full shadow-lg hover:scale-110 transition-all duration-200"
        >
          {theme === 'light' ? (
            <Moon size={18} className="text-gray-700 dark:text-gray-300" />
          ) : (
            <Sun size={18} className="text-yellow-500" />
          )}
        </button>
      </div>

      {/* Login Card */}
      <div className="w-full max-w-md">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-8 transition-colors duration-200">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-4">
              <Lock size={32} className="text-blue-600 dark:text-blue-400" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              {t.loginTitle}
            </h1>
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              {t.loginSubtitle}
            </p>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Access Code Input */}
            <div>
              <label 
                htmlFor="accessCode" 
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >
                {t.accessCode}
              </label>
              <input
                id="accessCode"
                type="text"
                value={code}
                onChange={handleCodeChange}
                placeholder={t.loginPlaceholder}
                disabled={isLoading}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all duration-200 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 font-mono text-center text-lg tracking-wider disabled:opacity-50 disabled:cursor-not-allowed"
                autoComplete="off"
                autoFocus
              />
            </div>

            {/* Error Message */}
            {error && (
              <div className="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg animate-shake">
                <AlertCircle size={20} className="text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-600 dark:text-red-400 font-medium">
                  {error}
                </p>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading || !code.trim()}
              className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl disabled:cursor-not-allowed disabled:hover:bg-gray-400 group"
            >
              {isLoading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>{t.verifying}</span>
                </>
              ) : (
                <>
                  <span>{t.loginButton}</span>
                  <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform duration-200" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Proxy Shop Admin Panel
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;

