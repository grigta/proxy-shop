import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { Key, ArrowRight, Copy, AlertTriangle, CheckCircle2, ShieldCheck, Loader2 } from 'lucide-react';
import { copyToClipboard as copyText } from '../lib/clipboard';

// Access code format constants
const VALID_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // Excludes I, O, 0, 1
const ACCESS_CODE_REGEX = /^[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{3}-[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{3}-[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{3}$/;

const Auth: React.FC = () => {
  const navigate = useNavigate();
  const { login, register, isLoading, error: authError, clearError } = useAuth();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [inputCode, setInputCode] = useState('');
  const [error, setError] = useState('');
  
  // Registration State
  const [generatedCode, setGeneratedCode] = useState<string | null>(null);
  const [hasCopied, setHasCopied] = useState(false);

  // Helper to format code as XXX-XXX-XXX
  const formatCode = (val: string) => {
    if (!val) return '';
    // Take only raw characters (no dashes)
    const raw = val.replace(/-/g, '');
    // Split into groups of 3
    const match = raw.match(/.{1,3}/g);
    return match ? match.join('-') : raw;
  };

  // Validate access code format
  const validateAccessCode = (code: string): boolean => {
    return ACCESS_CODE_REGEX.test(code);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    clearError();

    // Format the input code for validation
    const formattedCode = formatCode(inputCode);

    // Client-side validation
    if (!validateAccessCode(formattedCode)) {
      setError('Invalid Access Key. Must be XXX-XXX-XXX format.');
      return;
    }

    try {
      // Call async login
      await login(formattedCode);
      // On success, navigate to socks page
      navigate('/socks');
    } catch (err) {
      // Error is already set in AuthContext, display it
      // We can also set local error if needed
      console.error('Login error:', err);
    }
  };

  const handleGenerate = async () => {
    setError('');
    clearError();

    try {
      // Call async register - backend generates the code
      const code = await register();
      setGeneratedCode(code);
      setHasCopied(false);
    } catch (err) {
      // Error is already set in AuthContext
      console.error('Registration error:', err);
    }
  };

  const handleConfirmSaved = async () => {
    if (!generatedCode) return;
    
    setError('');
    clearError();

    try {
      await login(generatedCode);
      navigate('/socks');
    } catch (err) {
      console.error('Login error after registration:', err);
    }
  };

  const copyToClipboard = async () => {
    if (generatedCode) {
      // Copy the formatted code as displayed
      const success = await copyText(formatCode(generatedCode));
      if (success) {
        setHasCopied(true);
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-[#09090b] flex flex-col items-center justify-center p-4 transition-colors duration-200">
      
      <div className="mb-8 text-center cursor-pointer" onClick={() => navigate('/')}>
        <div className="flex items-center justify-center gap-2 mb-2">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-black dark:text-white">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">USE.NET</h1>
      </div>

      <div className="w-full max-w-md bg-white dark:bg-[#18181b] border border-gray-200 dark:border-[#27272a] rounded-2xl shadow-xl overflow-hidden transition-colors duration-200">
        
        {/* Tabs */}
        <div className="flex border-b border-gray-200 dark:border-[#27272a]">
          <button 
            onClick={() => { setMode('login'); setGeneratedCode(null); setError(''); clearError(); }}
            className={`flex-1 py-4 text-sm font-medium transition-colors ${mode === 'login' ? 'bg-white dark:bg-[#18181b] text-black dark:text-white border-b-2 border-black dark:border-white' : 'bg-gray-50 dark:bg-[#27272a] text-gray-500 dark:text-gray-400'}`}
          >
            Login
          </button>
          <button 
            onClick={() => { setMode('register'); setGeneratedCode(null); setError(''); clearError(); }}
            className={`flex-1 py-4 text-sm font-medium transition-colors ${mode === 'register' ? 'bg-white dark:bg-[#18181b] text-black dark:text-white border-b-2 border-black dark:border-white' : 'bg-gray-50 dark:bg-[#27272a] text-gray-500 dark:text-gray-400'}`}
          >
            New Access Key
          </button>
        </div>

        <div className="p-8">
          {mode === 'login' ? (
            <form onSubmit={handleLogin} className="space-y-6">
              <div>
                <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-2">Enter Access Code</label>
                <div className="relative">
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                    <Key size={18} />
                  </div>
                  <input 
                    type="text" 
                    value={formatCode(inputCode)}
                    onChange={(e) => {
                      // Strip all non-valid characters and convert to uppercase
                      const filtered = e.target.value
                        .toUpperCase()
                        .split('')
                        .filter(char => VALID_CHARS.includes(char))
                        .slice(0, 9) // Limit to 9 characters (raw, without dashes)
                        .join('');
                      setInputCode(filtered);
                      // Clear errors on input change
                      if (error) setError('');
                      if (authError) clearError();
                    }}
                    placeholder="ABC-DEF-GH2"
                    maxLength={11} // 9 characters + 2 dashes
                    className="w-full pl-10 pr-4 py-3 bg-gray-50 dark:bg-[#27272a] border border-gray-200 dark:border-[#3f3f46] rounded-lg focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white text-gray-900 dark:text-white font-mono tracking-widest text-center text-lg"
                  />
                </div>
                {(error || authError) && (
                  <p className="text-red-500 text-xs mt-2">{String(error || authError)}</p>
                )}
              </div>
              <button 
                type="submit" 
                disabled={isLoading}
                className="w-full py-3 bg-black dark:bg-white text-white dark:text-black rounded-lg font-bold hover:opacity-90 transition-opacity flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Loading...
                  </>
                ) : (
                  <>
                    Access Dashboard <ArrowRight size={16} />
                  </>
                )}
              </button>
            </form>
          ) : (
            <div>
              {!generatedCode ? (
                <div className="text-center">
                  <div className="w-16 h-16 bg-gray-100 dark:bg-[#27272a] rounded-full flex items-center justify-center mx-auto mb-6">
                    <ShieldCheck size={32} className="text-black dark:text-white" />
                  </div>
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">Generate Personal Access Key</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-8">
                    We do not use emails or passwords. Your Access Key is your only identity. Do not lose it.
                  </p>
                  {authError && (
                    <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-900/50 rounded-lg">
                      <p className="text-sm text-red-700 dark:text-red-400">{String(authError)}</p>
                    </div>
                  )}
                  <button 
                    onClick={handleGenerate} 
                    disabled={isLoading}
                    className="w-full py-3 bg-black dark:bg-white text-white dark:text-black rounded-lg font-bold hover:opacity-90 transition-opacity flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 size={16} className="animate-spin" />
                        Generating...
                      </>
                    ) : (
                      'Generate Key'
                    )}
                  </button>
                </div>
              ) : (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-900/50 rounded-xl p-4 mb-6 flex gap-3">
                    <AlertTriangle className="text-yellow-600 dark:text-yellow-500 flex-shrink-0" size={24} />
                    <div>
                      <h4 className="text-sm font-bold text-yellow-800 dark:text-yellow-500 mb-1">IMPORTANT</h4>
                      <p className="text-xs text-yellow-700 dark:text-yellow-400 leading-relaxed">
                        Save this code immediately. It will <strong>never</strong> be shown again. If you lose it, you lose access to your account and balance.
                      </p>
                    </div>
                  </div>

                  <div className="mb-6">
                    <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-2">Your Access Key</label>
                    <div onClick={copyToClipboard} className="group relative bg-gray-100 dark:bg-[#27272a] border border-gray-200 dark:border-[#3f3f46] rounded-xl p-4 text-center cursor-pointer hover:bg-gray-200 dark:hover:bg-[#3f3f46] transition-colors">
                        <p className="font-mono text-2xl font-bold text-black dark:text-white tracking-widest select-all">
                            {formatCode(generatedCode)}
                        </p>
                        <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-50 group-hover:opacity-100 transition-opacity">
                            {hasCopied ? <CheckCircle2 size={20} className="text-green-600" /> : <Copy size={20} />}
                        </div>
                    </div>
                    <p className="text-center mt-2 text-xs text-gray-400">
                      Click to copy • Format: XXX-XXX-XXX (excludes I, O, 0, 1)
                    </p>
                  </div>

                  <button 
                    onClick={handleConfirmSaved}
                    disabled={!hasCopied || isLoading}
                    className={`w-full py-3 rounded-lg font-bold flex items-center justify-center gap-2 transition-all ${
                        hasCopied && !isLoading
                        ? 'bg-black dark:bg-white text-white dark:text-black hover:opacity-90' 
                        : 'bg-gray-200 dark:bg-[#27272a] text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 size={16} className="animate-spin" />
                        Loading...
                      </>
                    ) : hasCopied ? (
                      "I have saved my Access Key"
                    ) : (
                      "Copy Key to Continue"
                    )}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Auth;