import React from 'react';
import { Crown, ShieldCheck, Zap, Gift, Users, ArrowUp, Star, MessageSquare, Headset } from 'lucide-react';
import { Tier } from '../types';

const TIERS: Tier[] = [
  {
    name: "Starter",
    code: "T0",
    proxyCount: "0+ proxies",
    discount: "0% Discount",
    features: ["Usual support"],
    isCurrent: false,
  },
  {
    name: "Premium",
    code: "T1",
    proxyCount: "250+ proxies",
    discount: "10% OFF",
    features: ["10% OFF", "Priority support"],
    isCurrent: false,
  },
  {
    name: "VIP",
    code: "T2",
    proxyCount: "500+ proxies",
    discount: "15% OFF",
    features: ["15% OFF", "Priority support"],
    isCurrent: false,
  },
  {
    name: "Elite",
    code: "T3",
    proxyCount: "750+ proxies",
    discount: "20% OFF",
    features: ["20% OFF", "Dedicated Support", "Custom features"],
    isCurrent: true, // Mocking user status
  },
];

const Loyalty: React.FC = () => {
  const currentTier = TIERS.find(t => t.isCurrent);

  return (
    <div className="min-h-full bg-gray-50 dark:bg-[#09090b] pb-20 transition-colors duration-200">
      <div className="max-w-5xl mx-auto px-6 pt-12">
        
        {/* Header */}
        <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gray-200/50 dark:bg-[#27272a] text-xs font-medium text-gray-600 dark:text-gray-300 mb-4">
                <Crown size={12} /> Loyalty Program
            </div>
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">Earn Rewards for <br/><span className="text-gray-400 dark:text-gray-500">Your Loyalty</span></h1>
            <p className="text-gray-500 dark:text-gray-400 max-w-xl mx-auto">The more proxies you purchase, the more benefits you unlock. Join our loyalty program and enjoy exclusive discounts, priority support, and special perks.</p>
        </div>

        {/* Current Status Card */}
        <div className="bg-gray-100 dark:bg-[#18181b] border border-gray-200 dark:border-[#27272a] rounded-2xl p-8 text-center mb-16 relative overflow-hidden transition-colors duration-200">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-gray-300 via-gray-500 to-gray-300 dark:from-gray-700 dark:via-gray-500 dark:to-gray-700 opacity-20"></div>
            <div className="w-12 h-12 bg-gray-200 dark:bg-[#27272a] rounded-full flex items-center justify-center mx-auto mb-4 transition-colors">
                <Crown size={24} className="text-gray-700 dark:text-gray-200" />
            </div>
            <h2 className="text-lg text-gray-600 dark:text-gray-400 font-medium mb-1">Your Current Tier</h2>
            <h3 className="text-3xl font-bold text-black dark:text-white mb-6">{currentTier?.name} ({currentTier?.code})</h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-2xl mx-auto">
                <div>
                    <p className="text-2xl font-bold text-black dark:text-white">{currentTier?.code}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Current Tier</p>
                </div>
                <div>
                    <p className="text-2xl font-bold text-black dark:text-white">{currentTier?.discount.replace(' OFF', '')}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Current Discount</p>
                </div>
                <div>
                    <div className="flex justify-center mb-1">
                        <div className="text-yellow-500">🏆</div>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Maximum tier reached!</p>
                </div>
            </div>
        </div>

        {/* Benefits */}
        <div className="mb-16">
            <h3 className="text-2xl font-bold text-center mb-8 text-gray-900 dark:text-white">Program Benefits</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {[
                    { icon: Zap, title: "Exclusive Discounts", desc: "Up to 20% off on all proxy purchases" },
                    { icon: ShieldCheck, title: "Priority Support", desc: "Faster response times and dedicated support" },
                    { icon: Star, title: "Premium Features", desc: "Access to exclusive features and integrations" },
                    { icon: Gift, title: "Special Rewards", desc: "Bonus credits and special promotions" }
                ].map((benefit, i) => (
                    <div key={i} className="bg-white dark:bg-[#18181b] border border-gray-100 dark:border-[#27272a] p-6 rounded-xl text-center hover:shadow-md transition-all">
                        <benefit.icon className="w-8 h-8 mx-auto mb-4 text-black dark:text-white" strokeWidth={1.5} />
                        <h4 className="font-bold text-gray-900 dark:text-white mb-2">{benefit.title}</h4>
                        <p className="text-sm text-gray-500 dark:text-gray-400">{benefit.desc}</p>
                    </div>
                ))}
            </div>
        </div>

        {/* All Tiers */}
        <div className="mb-20">
             <h3 className="text-2xl font-bold text-center mb-8 text-gray-900 dark:text-white">All Tiers</h3>
             <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {TIERS.map((tier, idx) => (
                    <div key={idx} className={`p-6 rounded-xl border transition-colors ${tier.isCurrent ? 'border-black dark:border-white ring-1 ring-black dark:ring-white bg-white dark:bg-[#18181b]' : 'border-gray-200 dark:border-[#27272a] bg-white dark:bg-[#18181b]'}`}>
                        <div className="w-10 h-10 bg-gray-100 dark:bg-[#27272a] text-black dark:text-white rounded-full flex items-center justify-center mx-auto mb-4 transition-colors">
                            {idx === 0 && <Users size={18} />}
                            {idx === 1 && <ArrowUp size={18} />}
                            {idx === 2 && <Star size={18} />}
                            {idx === 3 && <Crown size={18} />}
                        </div>
                        <div className="text-center mb-6">
                            <h4 className="font-bold text-gray-900 dark:text-white">{tier.name} ({tier.code})</h4>
                            <p className="text-xs text-gray-500 dark:text-gray-400">{tier.proxyCount}</p>
                        </div>
                        <div className="text-center mb-6">
                             <p className="text-xl font-bold text-gray-900 dark:text-white">{tier.discount}</p>
                        </div>
                        <ul className="space-y-2">
                            {tier.features.map((f, i) => (
                                <li key={i} className="flex items-start gap-2 text-xs text-gray-600 dark:text-gray-300">
                                    <div className="w-4 h-4 rounded-full border border-green-500 flex items-center justify-center flex-shrink-0">
                                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                                    </div>
                                    {f}
                                </li>
                            ))}
                        </ul>
                        {tier.isCurrent && (
                             <div className="mt-6 text-center">
                                <span className="bg-black dark:bg-white text-white dark:text-black text-xs px-4 py-2 rounded-lg inline-flex items-center gap-1 transition-colors">
                                    <Crown size={12} /> Current Tier
                                </span>
                             </div>
                        )}
                    </div>
                ))}
             </div>
        </div>

        {/* Support CTA */}
        <div className="bg-gray-100 dark:bg-[#18181b] rounded-2xl p-12 text-center transition-colors duration-200">
            <div className="inline-block p-3 bg-white dark:bg-[#27272a] rounded-full mb-4 text-black dark:text-white transition-colors">
                <MessageSquare size={24} />
            </div>
            <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-white">Have Any Questions?</h3>
            <p className="text-gray-500 dark:text-gray-400 text-sm mb-6 max-w-md mx-auto">Please contact our support team. We're here to help you understand our loyalty program and answer any questions you may have.</p>
            <button className="bg-black dark:bg-white text-white dark:text-black px-6 py-3 rounded-lg text-sm font-medium hover:bg-gray-800 dark:hover:bg-gray-200 transition-colors inline-flex items-center gap-2">
                <Headset size={16} /> Contact Support
            </button>
        </div>

      </div>
    </div>
  );
};

export default Loyalty;