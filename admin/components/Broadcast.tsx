import React, { useState, useEffect, useRef } from 'react';
import { Send, RefreshCw, X, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { Language } from '../types';
import { TRANSLATIONS } from '../constants';
import { adminApiClient } from '../lib/api-client';

interface BroadcastProps {
  lang: Language;
}

interface BroadcastItem {
  id: number;
  status: 'pending' | 'running' | 'completed' | 'cancelled';
  message_preview: string;
  total_users: number;
  sent_count: number;
  failed_count: number;
  created_at: string | null;
  completed_at: string | null;
}

const Broadcast: React.FC<BroadcastProps> = ({ lang }) => {
  const t = TRANSLATIONS[lang];

  // Form state
  const [messageText, setMessageText] = useState('');
  const [messagePhoto, setMessagePhoto] = useState('');
  const [filterLanguage, setFilterLanguage] = useState<string>('');

  // Loading states
  const [sendingTest, setSendingTest] = useState(false);
  const [sendingBroadcast, setSendingBroadcast] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);

  // Broadcasts history
  const [broadcasts, setBroadcasts] = useState<BroadcastItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Polling for running broadcasts
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch broadcasts history
  const fetchBroadcasts = async () => {
    try {
      setError(null);
      const response = await adminApiClient.getBroadcasts(20, 0);
      setBroadcasts(response.broadcasts || []);
    } catch (err: any) {
      console.error('Error fetching broadcasts:', err);
      setError(err.response?.data?.detail || 'Failed to load broadcasts');
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    fetchBroadcasts();

    // Start polling if there are running broadcasts
    pollingRef.current = setInterval(() => {
      fetchBroadcasts();
    }, 5000);

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  // Handle test send
  const handleSendTest = async () => {
    if (!messageText.trim()) {
      alert(lang === 'ru' ? 'Введите текст сообщения' : 'Enter message text');
      return;
    }

    setSendingTest(true);
    try {
      await adminApiClient.sendTestBroadcast(messageText, messagePhoto || undefined);
      alert(t.testSent);
    } catch (err: any) {
      console.error('Error sending test:', err);
      alert(err.response?.data?.detail || 'Failed to send test message');
    } finally {
      setSendingTest(false);
    }
  };

  // Handle broadcast send
  const handleSendBroadcast = async () => {
    if (!messageText.trim()) {
      alert(lang === 'ru' ? 'Введите текст сообщения' : 'Enter message text');
      return;
    }

    if (!confirm(t.confirmSend)) {
      return;
    }

    setSendingBroadcast(true);
    try {
      await adminApiClient.createBroadcast(
        messageText,
        messagePhoto || undefined,
        filterLanguage || undefined
      );
      alert(t.broadcastStarted);
      setMessageText('');
      setMessagePhoto('');
      setFilterLanguage('');
      fetchBroadcasts();
    } catch (err: any) {
      console.error('Error creating broadcast:', err);
      alert(err.response?.data?.detail || 'Failed to create broadcast');
    } finally {
      setSendingBroadcast(false);
    }
  };

  // Handle cancel broadcast
  const handleCancel = async (id: number) => {
    try {
      await adminApiClient.cancelBroadcast(id);
      fetchBroadcasts();
    } catch (err: any) {
      console.error('Error cancelling broadcast:', err);
      alert(err.response?.data?.detail || 'Failed to cancel broadcast');
    }
  };

  // Get status badge
  const getStatusBadge = (status: string) => {
    const badges: Record<string, { icon: any; class: string; label: string }> = {
      pending: {
        icon: Clock,
        class: 'bg-yellow-50 text-yellow-700 border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-300 dark:border-yellow-900/50',
        label: t.pending
      },
      running: {
        icon: RefreshCw,
        class: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/20 dark:text-blue-300 dark:border-blue-900/50',
        label: t.running
      },
      completed: {
        icon: CheckCircle,
        class: 'bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-300 dark:border-green-900/50',
        label: t.completed
      },
      cancelled: {
        icon: XCircle,
        class: 'bg-gray-100 text-gray-600 border-gray-200 dark:bg-gray-700 dark:text-gray-400 dark:border-gray-600',
        label: t.cancelled
      }
    };

    const badge = badges[status] || badges.pending;
    const Icon = badge.icon;

    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${badge.class}`}>
        <Icon size={12} className={status === 'running' ? 'animate-spin' : ''} />
        {badge.label}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{t.broadcast}</h2>
        <p className="text-gray-500 dark:text-gray-400 mt-1">{t.broadcastSubtitle}</p>
      </div>

      {/* Create Broadcast Form */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{t.createBroadcast}</h3>

        <div className="space-y-4">
          {/* Message Text */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t.messageText}
            </label>
            <textarea
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white text-sm resize-none"
              rows={5}
              placeholder={lang === 'ru' ? 'Введите текст сообщения (поддерживается HTML)...' : 'Enter message text (HTML supported)...'}
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              {lang === 'ru'
                ? 'Поддерживается HTML: <b>жирный</b>, <i>курсив</i>, <code>код</code>, <a href="url">ссылка</a>'
                : 'HTML supported: <b>bold</b>, <i>italic</i>, <code>code</code>, <a href="url">link</a>'
              }
            </p>
          </div>

          {/* Photo URL */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t.messagePhoto}
            </label>
            <input
              type="text"
              value={messagePhoto}
              onChange={(e) => setMessagePhoto(e.target.value)}
              className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white text-sm"
              placeholder="https://example.com/image.jpg"
            />
          </div>

          {/* Language Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t.filterLanguage}
            </label>
            <select
              value={filterLanguage}
              onChange={(e) => setFilterLanguage(e.target.value)}
              className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white text-sm"
            >
              <option value="">{t.allLanguages}</option>
              <option value="ru">{t.russian}</option>
              <option value="en">{t.english}</option>
            </select>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-2">
            <button
              onClick={handleSendTest}
              disabled={sendingTest || !messageText.trim()}
              className="px-4 py-2.5 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {sendingTest ? (
                <RefreshCw size={16} className="animate-spin" />
              ) : (
                <AlertCircle size={16} />
              )}
              {t.sendTest}
            </button>
            <button
              onClick={handleSendBroadcast}
              disabled={sendingBroadcast || !messageText.trim()}
              className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors shadow-sm shadow-blue-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {sendingBroadcast ? (
                <RefreshCw size={16} className="animate-spin" />
              ) : (
                <Send size={16} />
              )}
              {t.sendToAll}
            </button>
          </div>
        </div>
      </div>

      {/* Broadcast History */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="p-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t.broadcastHistory}</h3>
          <button
            onClick={fetchBroadcasts}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <RefreshCw size={18} />
          </button>
        </div>

        {loadingHistory && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}

        {error && (
          <div className="text-center py-12">
            <p className="text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        {!loadingHistory && !error && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 dark:bg-gray-900/50 text-gray-500 dark:text-gray-400 font-medium border-b border-gray-100 dark:border-gray-700">
                <tr>
                  <th className="px-6 py-4">ID</th>
                  <th className="px-6 py-4">{t.status}</th>
                  <th className="px-6 py-4">{t.messageText}</th>
                  <th className="px-6 py-4">{t.progress}</th>
                  <th className="px-6 py-4">{t.created}</th>
                  <th className="px-6 py-4 text-right">{t.actions}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {broadcasts.map((broadcast) => {
                  const progress = broadcast.total_users > 0
                    ? Math.round(((broadcast.sent_count + broadcast.failed_count) / broadcast.total_users) * 100)
                    : 0;

                  return (
                    <tr key={broadcast.id} className="hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
                      <td className="px-6 py-4 font-mono text-gray-900 dark:text-white">#{broadcast.id}</td>
                      <td className="px-6 py-4">{getStatusBadge(broadcast.status)}</td>
                      <td className="px-6 py-4 text-gray-600 dark:text-gray-300 max-w-xs truncate">
                        {broadcast.message_preview}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-blue-600 transition-all duration-300"
                              style={{ width: `${progress}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                            {broadcast.sent_count}/{broadcast.total_users}
                            {broadcast.failed_count > 0 && (
                              <span className="text-red-500 ml-1">({broadcast.failed_count} {t.failed})</span>
                            )}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-gray-500 dark:text-gray-400 whitespace-nowrap">
                        {broadcast.created_at
                          ? new Date(broadcast.created_at).toLocaleString(lang === 'ru' ? 'ru-RU' : 'en-US', {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            })
                          : '-'
                        }
                      </td>
                      <td className="px-6 py-4 text-right">
                        {(broadcast.status === 'pending' || broadcast.status === 'running') && (
                          <button
                            onClick={() => handleCancel(broadcast.id)}
                            className="text-gray-400 hover:text-red-600 transition-colors"
                            title={t.cancelBroadcast}
                          >
                            <X size={16} />
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
                {broadcasts.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                      {t.noHistory}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Broadcast;
