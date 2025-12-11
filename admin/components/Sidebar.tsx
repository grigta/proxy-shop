import React from 'react';
import { LayoutDashboard, Users, Tag, Server, LogOut, Send } from 'lucide-react';
import { View, Language } from '../types';
import { TRANSLATIONS } from '../constants';

interface SidebarProps {
  currentView: View;
  onChangeView: (view: View) => void;
  lang: Language;
  onLogout?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ currentView, onChangeView, lang, onLogout }) => {
  const t = TRANSLATIONS[lang];

  const menuItems = [
    { id: 'dashboard' as View, label: t.dashboard, icon: LayoutDashboard },
    { id: 'users' as View, label: t.users, icon: Users },
    { id: 'coupons' as View, label: t.coupons, icon: Tag },
    { id: 'proxies' as View, label: t.proxies, icon: Server },
    { id: 'broadcast' as View, label: t.broadcast, icon: Send },
  ];

  return (
    <div className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 h-screen flex flex-col fixed left-0 top-0 z-30 hidden md:flex transition-colors duration-200">
      <div className="p-6 border-b border-gray-100 dark:border-gray-700">
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">{t.adminTitle}</h1>
      </div>
      
      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onChangeView(item.id)}
            className={`w-full flex items-center px-4 py-3 rounded-lg transition-colors duration-200 text-sm font-medium ${
              currentView === item.id
                ? 'bg-blue-600 text-white shadow-md shadow-blue-500/30'
                : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            <item.icon size={20} className="mr-3" />
            {item.label}
          </button>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-100 dark:border-gray-700">
        <button 
          onClick={onLogout}
          className="w-full flex items-center px-4 py-3 text-gray-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors text-sm font-medium"
        >
          <LogOut size={20} className="mr-3" />
          {t.logout}
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
