import React, { useState, useMemo, useEffect } from 'react';
import { DollarSign, CreditCard, Server, Network, RotateCcw, Filter, Calendar, TrendingUp } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Language, DashboardStatsResponse, RevenueChartData } from '../types';
import { TRANSLATIONS } from '../constants';
import { adminApiClient } from '../lib/api-client';

interface DashboardProps {
  lang: Language;
}

type Period = 'today' | 'week' | 'month' | 'all';

const Dashboard: React.FC<DashboardProps> = ({ lang }) => {
  const t = TRANSLATIONS[lang];
  const [selectedPeriod, setSelectedPeriod] = useState<Period>('month');
  const [selectedUser, setSelectedUser] = useState<number | 'all'>('all');

  // State for API data
  const [dashboardStats, setDashboardStats] = useState<DashboardStatsResponse | null>(null);
  const [chartData, setChartData] = useState<RevenueChartData[]>([]);
  const [activityLog, setActivityLog] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch dashboard stats from API
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [statsData, chartDataResponse, activityData] = await Promise.all([
          adminApiClient.getDashboardStats(),
          adminApiClient.getRevenueChart(selectedPeriod === 'today' ? '1d' : selectedPeriod === 'week' ? '7d' : selectedPeriod === 'month' ? '30d' : 'all'),
          adminApiClient.getRecentActivity(10)
        ]);

        setDashboardStats(statsData);
        setChartData(chartDataResponse);
        setActivityLog(activityData);
      } catch (err: any) {
        console.error('Error fetching dashboard data:', err);
        setError(err.response?.data?.detail || 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [selectedPeriod]);

  // Calculate stats based on selected period
  const stats = useMemo(() => {
    if (!dashboardStats) {
      return {
        depositsSum: '0.00',
        depositsCount: 0,
        pptpSales: '0.00',
        proxySales: '0.00',
        refundsCount: 0,
        netProfit: '0.00',
        depositsChangePercent: 0,
        usersChangePercent: 0,
        pptpChangePercent: 0,
        proxyChangePercent: 0,
        refundsChangePercent: 0,
        netProfitChangePercent: 0,
      };
    }

    const periodKey = selectedPeriod === 'today' ? '1d' : selectedPeriod === 'week' ? '7d' : selectedPeriod === 'month' ? '30d' : 'all_time';
    const periodStats = dashboardStats.period_stats[periodKey];

    const formatValue = (val: any) => typeof val === 'number' ? val.toFixed(2) : parseFloat(val.toString()).toFixed(2);
    const formatPercent = (val: any) => {
      const num = typeof val === 'number' ? val : parseFloat(val.toString());
      return num >= 0 ? `+${num.toFixed(1)}%` : `${num.toFixed(1)}%`;
    };

    return {
      depositsSum: formatValue(periodStats.deposits),
      depositsCount: periodStats.deposits_count || 0,
      pptpSales: formatValue(periodStats.pptp_revenue || 0),
      proxySales: formatValue(periodStats.proxy_revenue || 0),
      refundsCount: periodStats.refunds,
      netProfit: formatValue(periodStats.net_profit || 0),
      depositsChangePercent: formatPercent(periodStats.deposits_change_percent || 0),
      usersChangePercent: formatPercent(periodStats.users_change_percent || 0),
      pptpChangePercent: formatPercent(periodStats.pptp_revenue_change_percent || 0),
      proxyChangePercent: formatPercent(periodStats.proxy_revenue_change_percent || 0),
      refundsChangePercent: formatPercent(periodStats.refunds_change_percent || 0),
      netProfitChangePercent: formatPercent(periodStats.net_profit_change_percent || 0),
    };
  }, [dashboardStats, selectedPeriod]);

  const statCards = [
    {
      title: t.depositsSum,
      value: `$${stats.depositsSum}`,
      icon: DollarSign,
      color: 'text-green-600',
      bg: 'bg-green-100 dark:bg-green-900/20',
      trend: stats.depositsChangePercent
    },
    {
      title: t.depositsCount,
      value: stats.depositsCount,
      icon: CreditCard,
      color: 'text-blue-600',
      bg: 'bg-blue-100 dark:bg-blue-900/20',
      trend: stats.depositsChangePercent
    },
    {
      title: t.pptpSales,
      value: `$${stats.pptpSales}`,
      icon: Network,
      color: 'text-purple-600',
      bg: 'bg-purple-100 dark:bg-purple-900/20',
      trend: stats.pptpChangePercent
    },
    {
      title: t.proxySales,
      value: `$${stats.proxySales}`,
      icon: Server,
      color: 'text-indigo-600',
      bg: 'bg-indigo-100 dark:bg-indigo-900/20',
      trend: stats.proxyChangePercent
    },
    {
      title: t.refundsCount,
      value: stats.refundsCount,
      icon: RotateCcw,
      color: 'text-red-600',
      bg: 'bg-red-100 dark:bg-red-900/20',
      trend: stats.refundsChangePercent
    },
    {
      title: t.netProfit,
      value: `$${stats.netProfit}`,
      icon: TrendingUp,
      color: 'text-emerald-600',
      bg: 'bg-emerald-100 dark:bg-emerald-900/20',
      trend: stats.netProfitChangePercent
    },
  ];

  // Show loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-500 dark:text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <p className="text-red-600 dark:text-red-400">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-end gap-4 mb-8">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{t.dashboard}</h2>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{t.financialOverview}</p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 w-full lg:w-auto">
          {/* Period Filter */}
          <div className="flex bg-white dark:bg-gray-800 p-1 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
            {(['today', 'week', 'month', 'all'] as Period[]).map((p) => (
              <button
                key={p}
                onClick={() => setSelectedPeriod(p)}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${
                  selectedPeriod === p
                    ? 'bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 shadow-md'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                {p === 'today' ? t.periodToday : 
                 p === 'week' ? t.periodWeek : 
                 p === 'month' ? t.periodMonth : t.periodAll}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {statCards.map((stat, index) => (
          <div key={index} className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md transition-shadow relative overflow-hidden group">
            <div className="flex justify-between items-start mb-4">
              <div className={`p-2.5 rounded-lg ${stat.bg}`}>
                <stat.icon className={`w-5 h-5 ${stat.color}`} />
              </div>
              <span className={`text-xs font-medium px-2 py-1 rounded-full ${stat.trend.startsWith('+') ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400'}`}>
                {stat.trend}
              </span>
            </div>
            <div>
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</h3>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mt-1">{stat.title}</p>
            </div>
            {/* Decoration */}
            <div className="absolute -right-6 -bottom-6 opacity-[0.03] dark:opacity-[0.05] group-hover:scale-110 transition-transform duration-300">
              <stat.icon className="w-24 h-24" />
            </div>
          </div>
        ))}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">{t.revenueChart}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Revenue vs Purchases</p>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-blue-500"></span> Revenue
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-purple-500"></span> Purchases
              </span>
            </div>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData.map(item => ({
                name: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                revenue: typeof item.revenue === 'number' ? item.revenue : parseFloat(item.revenue.toString()),
                purchases: item.purchases
              }))}>
                <defs>
                  <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorPur" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#374151" opacity={0.1} />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#9ca3af', fontSize: 12}} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#9ca3af', fontSize: 12}} dx={-10} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px', color: '#fff' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Area type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorRev)" />
                <Area type="monotone" dataKey="purchases" stroke="#a855f7" strokeWidth={2} fillOpacity={1} fill="url(#colorPur)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
           <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Activity Log</h3>
           <div className="space-y-4">
              {activityLog.length > 0 ? (
                activityLog.slice(0, 5).map((activity) => {
                  const isInflow = activity.action_type === 'DEPOSIT' || activity.action_type === 'REFUND';
                  const isOutflow = activity.action_type === 'BUY_SOCKS5' || activity.action_type === 'BUY_PPTP';
                  const timeAgo = activity.timestamp ? new Date(activity.timestamp).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Unknown';

                  return (
                    <div key={activity.id} className="flex items-center gap-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-lg transition-colors cursor-pointer">
                       <div className={`w-8 h-8 rounded-full ${isInflow ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400' : 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'} flex items-center justify-center text-xs font-bold`}>
                          {isInflow ? 'IN' : 'OUT'}
                       </div>
                       <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {activity.action_type === 'DEPOSIT' ? 'Deposit' : activity.action_type === 'BUY_SOCKS5' ? 'Bought SOCKS5' : activity.action_type === 'BUY_PPTP' ? 'Bought PPTP' : activity.action_type === 'REFUND' ? 'Refund' : activity.action_type}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">{timeAgo}</p>
                       </div>
                       {activity.amount_change !== null && activity.amount_change !== undefined && (
                         <div className={`text-sm font-bold ${activity.amount_change >= 0 ? 'text-green-600' : 'text-red-600 dark:text-red-400'}`}>
                            {activity.amount_change >= 0 ? '+' : ''}${Math.abs(activity.amount_change).toFixed(2)}
                         </div>
                       )}
                    </div>
                  );
                })
              ) : (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  No recent activity
                </div>
              )}
           </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;