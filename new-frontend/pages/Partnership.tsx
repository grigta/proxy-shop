import React from 'react';
import { Gift, Send, CheckCircle2, Users, DollarSign, ArrowRight, Command, Zap, Star } from 'lucide-react';

const Partnership: React.FC = () => {
  return (
    <div className="min-h-full bg-gray-50 dark:bg-[#09090b] pb-20 transition-colors duration-200">
      <div className="max-w-6xl mx-auto px-6 pt-12">

        {/* Hero Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center mb-24">
            <div>
                <div className="inline-flex items-center gap-2 text-xs font-medium text-gray-600 dark:text-gray-300 mb-6">
                    <Gift size={14} /> Earn up to 20% commission
                </div>
                <h1 className="text-5xl font-bold text-gray-900 dark:text-white mb-6 leading-tight">
                    Join the Elusive.sh <br/> <span className="text-gray-400 dark:text-gray-500">affiliate program</span>
                </h1>
                <p className="text-gray-600 dark:text-gray-400 mb-8 max-w-md leading-relaxed">
                    When you join the program, you can earn commissions for new users who make their first purchase using your referral code.
                </p>
                <div className="flex items-center gap-6">
                    <button className="bg-black dark:bg-white text-white dark:text-black px-6 py-3 rounded-lg font-medium hover:bg-gray-800 dark:hover:bg-gray-200 transition-colors inline-flex items-center gap-2">
                        <Send size={16} /> Apply Now
                    </button>
                    <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                        <CheckCircle2 size={16} className="text-green-600 dark:text-green-500" /> Free to join
                    </div>
                </div>

                {/* Mini Stats */}
                <div className="grid grid-cols-3 gap-8 mt-16 border-t border-gray-200 dark:border-[#27272a] pt-8">
                    <div>
                        <p className="text-3xl font-bold text-black dark:text-white">20%</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Commission</p>
                    </div>
                    <div>
                        <p className="text-3xl font-bold text-black dark:text-white">100+</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Partners</p>
                    </div>
                    <div>
                        <p className="text-3xl font-bold text-black dark:text-white">$10K+</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Paid Out</p>
                    </div>
                </div>
            </div>
            <div className="flex justify-center">
                 {/* Abstract Bird Logo Representation */}
                 <svg width="400" height="400" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg" className="drop-shadow-2xl">
                    <path fillRule="evenodd" clipRule="evenodd" d="M100 180C144.183 180 180 144.183 180 100C180 55.8172 144.183 20 100 20C55.8172 20 20 55.8172 20 100C20 144.183 55.8172 180 100 180ZM100 150L130 100H70L100 150Z" className="fill-black dark:fill-white transition-colors"/>
                    <path d="M60 80H140L100 140L60 80Z" className="fill-white dark:fill-black transition-colors"/>
                    <circle cx="85" cy="70" r="5" className="fill-white dark:fill-black transition-colors"/>
                    <circle cx="115" cy="70" r="5" className="fill-white dark:fill-black transition-colors"/>
                 </svg>
            </div>
        </div>

        {/* Process Section */}
        <div className="mb-24">
            <div className="text-center mb-16">
                 <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gray-200/50 dark:bg-[#27272a] text-xs font-medium text-gray-600 dark:text-gray-300 mb-4 transition-colors">
                    <Command size={12} /> Simple Process
                </div>
                <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">How we work with affiliate partners</h2>
                <p className="text-gray-500 dark:text-gray-400 max-w-xl mx-auto">Our affiliate program is designed to be simple and rewarding. Here's how the process works.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
                {/* Connecting Line (Desktop only) */}
                <div className="hidden md:block absolute top-8 left-[16%] right-[16%] h-px bg-dashed border-t border-gray-300 dark:border-gray-700 -z-10"></div>

                {[
                    { 
                        step: "1", 
                        icon: Send, 
                        title: "Apply", 
                        desc: "Fill out a simple form to become an affiliate partner and receive your unique referral code.",
                        sub: "Instant approval",
                        subIcon: CheckCircle2
                    },
                    { 
                        step: "2", 
                        icon: Users, 
                        title: "Promote Elusive.sh", 
                        desc: "Recommend our SOCKS5 proxy services to your audience using your referral code.",
                        sub: "Marketing materials provided",
                        subIcon: ArrowRight
                    },
                    { 
                        step: "3", 
                        icon: DollarSign, 
                        title: "Earn commissions", 
                        desc: "Receive revenue for qualified first purchases made using your referral code.",
                        sub: "Weekly payouts",
                        subIcon: Zap
                    }
                ].map((item, i) => (
                    <div key={i} className="bg-white dark:bg-[#18181b] p-8 rounded-xl border border-gray-200 dark:border-[#27272a] relative transition-colors duration-200">
                        <div className="absolute -top-4 -right-4 w-8 h-8 bg-black dark:bg-white text-white dark:text-black rounded-full flex items-center justify-center text-sm font-bold border-4 border-gray-50 dark:border-[#18181b] transition-colors">
                            {item.step}
                        </div>
                        <div className="w-12 h-12 bg-gray-900 dark:bg-white rounded-lg flex items-center justify-center mb-6 text-white dark:text-black transition-colors">
                            <item.icon size={24} />
                        </div>
                        <h3 className="text-xl font-bold mb-3 text-gray-900 dark:text-white">{item.title}</h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed mb-6 h-16">{item.desc}</p>
                        <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 pt-4 border-t border-gray-100 dark:border-[#27272a]">
                             <item.subIcon size={14} /> {item.sub}
                        </div>
                    </div>
                ))}
            </div>
        </div>

        {/* CTA Footer */}
        <div className="text-center">
             <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gray-100 dark:bg-[#18181b] text-xs font-medium text-gray-600 dark:text-gray-300 mb-4 transition-colors">
                 <Star size={12} /> Ready to Start
             </div>
             <h2 className="text-3xl font-bold mb-4 text-gray-900 dark:text-white">Ready to start earning?</h2>
             <p className="text-gray-500 dark:text-gray-400 mb-8">Join our affiliate program and start earning commissions today. It's free to join and takes less than 5 minutes to get started.</p>
             <div className="flex items-center justify-center gap-6">
                 <button className="bg-black dark:bg-white text-white dark:text-black px-8 py-3 rounded-lg font-medium hover:bg-gray-800 dark:hover:bg-gray-200 transition-colors flex items-center gap-2">
                    <Send size={16} /> Get Started
                 </button>
                 <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                     <CheckCircle2 size={14} /> No setup fees • Instant approval
                 </div>
             </div>
        </div>

      </div>
    </div>
  );
};

export default Partnership;