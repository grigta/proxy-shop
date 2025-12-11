import React, { useState, useMemo } from 'react';
import { Search, Signal, SignalHigh, SignalLow, Wifi, Server, Smartphone, ChevronDown, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { ProxyType, SpeedLevel, ProxyNode } from '../types';

// Mock Data
const MOCK_PROXIES: ProxyNode[] = Array.from({ length: 30 }).map((_, i) => ({
  id: `px-${i}`,
  ip: `192.168.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
  country: 'US',
  city: ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Miami'][Math.floor(Math.random() * 5)],
  region: ['NY', 'CA', 'IL', 'TX', 'FL'][Math.floor(Math.random() * 5)],
  isp: ['Comcast Cable', 'AT&T Internet', 'Verizon Business', 'T-Mobile USA', 'Charter Communications'][Math.floor(Math.random() * 5)],
  zip: Math.floor(10000 + Math.random() * 90000).toString(),
  speed: [SpeedLevel.FAST, SpeedLevel.MODERATE, SpeedLevel.SLOW][Math.floor(Math.random() * 3)],
  type: [ProxyType.RESIDENTIAL, ProxyType.MOBILE, ProxyType.DATACENTER][Math.floor(Math.random() * 3)],
  price: 1.60
}));

const Dashboard: React.FC = () => {
  const [proxies] = useState<ProxyNode[]>(MOCK_PROXIES);
  const [filterType, setFilterType] = useState<string>('All');
  const [filterSpeed, setFilterSpeed] = useState<string>('All');
  const [sortConfig, setSortConfig] = useState<{ key: keyof ProxyNode; direction: 'asc' | 'desc' } | null>(null);

  const processedProxies = useMemo(() => {
    // 1. Filter
    let result = proxies.filter(proxy => {
      const matchesType = filterType === 'All' || proxy.type === filterType;
      const matchesSpeed = filterSpeed === 'All' || proxy.speed === filterSpeed;
      return matchesType && matchesSpeed;
    });

    // 2. Sort
    if (sortConfig !== null) {
      result.sort((a, b) => {
        // Custom Sort for Speed
        if (sortConfig.key === 'speed') {
            const speedWeight = { [SpeedLevel.FAST]: 3, [SpeedLevel.MODERATE]: 2, [SpeedLevel.SLOW]: 1 };
            const aVal = speedWeight[a.speed];
            const bVal = speedWeight[b.speed];
            if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
            return 0;
        }

        // Custom Sort for IP
        if (sortConfig.key === 'ip') {
            const aParts = a.ip.split('.').map(Number);
            const bParts = b.ip.split('.').map(Number);
            for(let i=0; i<4; i++) {
                if (aParts[i] < bParts[i]) return sortConfig.direction === 'asc' ? -1 : 1;
                if (aParts[i] > bParts[i]) return sortConfig.direction === 'asc' ? 1 : -1;
            }
            return 0;
        }

        // Default Sort
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }

    return result;
  }, [proxies, filterType, filterSpeed, sortConfig]);

  const handleSort = (key: keyof ProxyNode) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const SortIcon = ({ columnKey }: { columnKey: keyof ProxyNode }) => {
    const isActive = sortConfig?.key === columnKey;
    return (
        <span className="inline-flex flex-col justify-center h-4 w-4 ml-1 align-middle">
            {isActive ? (
                sortConfig.direction === 'asc' ? (
                    <ArrowUp size={14} className="text-black dark:text-white" />
                ) : (
                    <ArrowDown size={14} className="text-black dark:text-white" />
                )
            ) : (
                <ArrowUpDown size={14} className="text-gray-300 dark:text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" />
            )}
        </span>
    );
  };

  const SpeedIcon = ({ speed }: { speed: SpeedLevel }) => {
    if (speed === SpeedLevel.FAST) return <SignalHigh size={16} className="text-green-600 dark:text-green-500" />;
    if (speed === SpeedLevel.MODERATE) return <Signal size={16} className="text-yellow-600 dark:text-yellow-500" />;
    return <SignalLow size={16} className="text-red-600 dark:text-red-500" />;
  };

  const TypeIcon = ({ type }: { type: ProxyType }) => {
    if (type === ProxyType.RESIDENTIAL) return <div className="flex items-center gap-1"><Wifi size={14} /> Residential</div>;
    if (type === ProxyType.MOBILE) return <div className="flex items-center gap-1"><Smartphone size={14} /> Mobile</div>;
    return <div className="flex items-center gap-1"><Server size={14} /> Hosting</div>;
  };

  return (
    <div className="p-6 bg-gray-50 dark:bg-[#09090b] min-h-full transition-colors duration-200">
      {/* Top Controls */}
      <div className="bg-white dark:bg-[#18181b] p-4 rounded-xl border border-gray-200 dark:border-[#27272a] shadow-sm mb-6 transition-colors duration-200">
        <div className="flex flex-col md:flex-row gap-4 items-end">
            <div className="flex-1 grid grid-cols-2 md:grid-cols-5 gap-4 w-full">
                <div>
                    <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1 block">Country</label>
                    <select className="w-full bg-gray-50 dark:bg-[#27272a] border border-gray-200 dark:border-[#3f3f46] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black dark:focus:ring-white text-gray-900 dark:text-white transition-colors">
                        <option>United States</option>
                        <option>United Kingdom</option>
                        <option>Canada</option>
                    </select>
                </div>
                <div>
                    <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1 block">State</label>
                    <input type="text" placeholder="NY" className="w-full bg-gray-50 dark:bg-[#27272a] border border-gray-200 dark:border-[#3f3f46] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black dark:focus:ring-white text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 transition-colors" />
                </div>
                <div>
                    <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1 block">City</label>
                    <input type="text" placeholder="New York" className="w-full bg-gray-50 dark:bg-[#27272a] border border-gray-200 dark:border-[#3f3f46] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black dark:focus:ring-white text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 transition-colors" />
                </div>
                <div>
                    <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1 block">Zip</label>
                    <input type="text" placeholder="10001" className="w-full bg-gray-50 dark:bg-[#27272a] border border-gray-200 dark:border-[#3f3f46] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black dark:focus:ring-white text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 transition-colors" />
                </div>
                <div>
                    <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1 block">Zip Radius</label>
                    <select className="w-full bg-gray-50 dark:bg-[#27272a] border border-gray-200 dark:border-[#3f3f46] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-black dark:focus:ring-white text-gray-900 dark:text-white transition-colors">
                        <option>None</option>
                        <option>10 miles</option>
                        <option>50 miles</option>
                    </select>
                </div>
            </div>
            <button className="bg-gray-100 dark:bg-[#27272a] hover:bg-gray-200 dark:hover:bg-[#3f3f46] p-2 rounded-lg transition-colors border border-gray-200 dark:border-[#3f3f46] h-[38px] w-[38px] flex items-center justify-center flex-shrink-0">
                <Search size={20} className="text-gray-600 dark:text-gray-300" />
            </button>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="flex justify-end gap-2 mb-4">
        <div className="flex items-center gap-2 bg-white dark:bg-[#18181b] border border-gray-200 dark:border-[#27272a] rounded-lg px-3 py-1.5 transition-colors">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Type</span>
            <div className="relative">
              <select 
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="text-xs font-semibold pl-2 pr-6 py-0.5 rounded bg-gray-100 dark:bg-[#27272a] text-gray-900 dark:text-white transition-colors appearance-none focus:outline-none cursor-pointer border-none"
              >
                <option value="All">All</option>
                {Object.values(ProxyType).map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
              <ChevronDown size={12} className="absolute right-1.5 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" />
            </div>
        </div>
        <div className="flex items-center gap-2 bg-white dark:bg-[#18181b] border border-gray-200 dark:border-[#27272a] rounded-lg px-3 py-1.5 transition-colors">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Speed</span>
            <div className="relative">
              <select 
                value={filterSpeed}
                onChange={(e) => setFilterSpeed(e.target.value)}
                className="text-xs font-semibold pl-2 pr-6 py-0.5 rounded bg-gray-100 dark:bg-[#27272a] text-gray-900 dark:text-white transition-colors appearance-none focus:outline-none cursor-pointer border-none"
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
                <th className="px-6 py-3 font-medium cursor-pointer group select-none hover:bg-gray-100 dark:hover:bg-[#3f3f46] transition-colors" onClick={() => handleSort('ip')}>
                    <div className="flex items-center">Proxy IP <SortIcon columnKey="ip" /></div>
                </th>
                <th className="px-6 py-3 font-medium cursor-pointer group select-none hover:bg-gray-100 dark:hover:bg-[#3f3f46] transition-colors" onClick={() => handleSort('country')}>
                    <div className="flex items-center">Country <SortIcon columnKey="country" /></div>
                </th>
                <th className="px-6 py-3 font-medium cursor-pointer group select-none hover:bg-gray-100 dark:hover:bg-[#3f3f46] transition-colors" onClick={() => handleSort('city')}>
                    <div className="flex items-center">City <SortIcon columnKey="city" /></div>
                </th>
                <th className="px-6 py-3 font-medium cursor-pointer group select-none hover:bg-gray-100 dark:hover:bg-[#3f3f46] transition-colors" onClick={() => handleSort('region')}>
                    <div className="flex items-center">Region <SortIcon columnKey="region" /></div>
                </th>
                <th className="px-6 py-3 font-medium cursor-pointer group select-none hover:bg-gray-100 dark:hover:bg-[#3f3f46] transition-colors" onClick={() => handleSort('isp')}>
                    <div className="flex items-center">ISP <SortIcon columnKey="isp" /></div>
                </th>
                <th className="px-6 py-3 font-medium cursor-pointer group select-none hover:bg-gray-100 dark:hover:bg-[#3f3f46] transition-colors" onClick={() => handleSort('zip')}>
                    <div className="flex items-center">Zip <SortIcon columnKey="zip" /></div>
                </th>
                <th className="px-6 py-3 font-medium cursor-pointer group select-none hover:bg-gray-100 dark:hover:bg-[#3f3f46] transition-colors" onClick={() => handleSort('speed')}>
                    <div className="flex items-center">Speed <SortIcon columnKey="speed" /></div>
                </th>
                <th className="px-6 py-3 font-medium cursor-pointer group select-none hover:bg-gray-100 dark:hover:bg-[#3f3f46] transition-colors" onClick={() => handleSort('type')}>
                    <div className="flex items-center">Type <SortIcon columnKey="type" /></div>
                </th>
                <th className="px-6 py-3 font-medium text-right cursor-pointer group select-none hover:bg-gray-100 dark:hover:bg-[#3f3f46] transition-colors" onClick={() => handleSort('price')}>
                    <div className="flex items-center justify-end">Buy <SortIcon columnKey="price" /></div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-[#27272a]">
              {processedProxies.length > 0 ? (
                processedProxies.map((proxy) => (
                  <tr key={proxy.id} className="hover:bg-gray-50 dark:hover:bg-[#27272a] transition-colors text-gray-900 dark:text-gray-300">
                    <td className="px-6 py-4 font-mono text-gray-700 dark:text-gray-300">{proxy.ip}</td>
                    <td className="px-6 py-4">{proxy.country}</td>
                    <td className="px-6 py-4">{proxy.city}</td>
                    <td className="px-6 py-4">{proxy.region}</td>
                    <td className="px-6 py-4 truncate max-w-[150px]" title={proxy.isp}>{proxy.isp}</td>
                    <td className="px-6 py-4 font-mono text-gray-500 dark:text-gray-500">{proxy.zip}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                          <SpeedIcon speed={proxy.speed} />
                          <span className="text-xs font-medium">{proxy.speed}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-[#27272a] text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-[#3f3f46]">
                           <TypeIcon type={proxy.type} />
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button className="inline-flex items-center gap-1 px-3 py-1.5 bg-white dark:bg-[#18181b] border border-gray-200 dark:border-[#3f3f46] rounded-lg text-xs font-medium hover:bg-black dark:hover:bg-white hover:text-white dark:hover:text-black hover:border-black dark:hover:border-white transition-all text-gray-900 dark:text-gray-100">
                          <span>${proxy.price.toFixed(2)}</span>
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={9} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                    No proxies found matching your filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="px-6 py-4 border-t border-gray-200 dark:border-[#27272a] bg-gray-50 dark:bg-[#18181b] flex justify-between items-center transition-colors">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Showing {processedProxies.length} proxies
            </span>
            <div className="flex gap-2">
                <button className="px-3 py-1 border border-gray-300 dark:border-[#3f3f46] rounded text-xs bg-white dark:bg-[#27272a] text-gray-900 dark:text-gray-200 disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-[#3f3f46] transition-colors">Previous</button>
                <button className="px-3 py-1 border border-gray-300 dark:border-[#3f3f46] rounded text-xs bg-white dark:bg-[#27272a] text-gray-900 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-[#3f3f46] transition-colors">Next</button>
            </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;