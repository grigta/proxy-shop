import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Wifi, Shield, Database, Plus, Minus, ArrowRight, Check, Globe, Server, Smartphone } from 'lucide-react';
import { FaqItem } from '../types';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  
  const FAQ_DATA: FaqItem[] = [
    { question: "Are there logs?", answer: "No, we do not keep any logs of your activity. Your privacy is paramount." },
    { question: "What payment methods are accepted?", answer: "We accept major credit cards, PayPal, and various cryptocurrencies." },
    { question: "Are there any offers for bulk orders?", answer: "Yes, please contact our sales team for custom bulk pricing." },
    { question: "What are the refund policies?", answer: "We offer a 3-day money-back guarantee if the service does not meet your needs." },
  ];

  return (
    <div className="min-h-screen bg-white dark:bg-black text-gray-900 dark:text-gray-100 font-sans transition-colors duration-200">
      
      {/* Navbar */}
      <nav className="sticky top-0 z-50 bg-white/80 dark:bg-black/80 backdrop-blur-md border-b border-gray-100 dark:border-neutral-900 transition-colors">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-xl tracking-tight text-black dark:text-white">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-black dark:text-white transition-colors">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            USE.NET
          </div>
          
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-600 dark:text-gray-400">
            <a href="#features" className="hover:text-black dark:hover:text-white transition-colors">Features</a>
            <a href="#pricing" className="hover:text-black dark:hover:text-white transition-colors">Pricing</a>
            <a href="#contact" className="hover:text-black dark:hover:text-white transition-colors">Contact</a>
          </div>

          <button onClick={() => navigate('/auth')} className="text-sm font-medium px-5 py-2 bg-gray-100 dark:bg-neutral-900 hover:bg-gray-200 dark:hover:bg-neutral-800 rounded-full transition-colors text-gray-900 dark:text-white">
            Sign In
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-24 pb-20 px-6 text-center max-w-5xl mx-auto">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400 text-xs font-medium mb-8 border border-orange-100 dark:border-orange-900/50">
           <span className="w-2 h-2 rounded-full bg-orange-500 animate-pulse"></span> Truly Residential Proxies <ArrowRight size={12} />
        </div>
        
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-gray-900 dark:text-white mb-8 leading-tight">
          Don't Get Blocked,<br />
          <span className="text-gray-400 dark:text-gray-600">Get USE.NET</span>
        </h1>
        
        <p className="text-xl text-gray-500 dark:text-gray-400 max-w-2xl mx-auto mb-10 font-light">
          Experience true anonymity with unlimited residential SOCKS5 proxies.
        </p>

        <button onClick={() => navigate('/auth')} className="bg-black dark:bg-white text-white dark:text-black px-8 py-4 rounded-full font-medium hover:bg-gray-800 dark:hover:bg-gray-200 transition-all transform hover:scale-105 flex items-center gap-2 mx-auto mb-20 shadow-xl shadow-gray-200 dark:shadow-none">
          Get Started <ArrowRight size={18} />
        </button>

        {/* Dashboard Preview Mockup */}
        <div className="rounded-2xl overflow-hidden border border-gray-200 dark:border-neutral-800 shadow-2xl mx-auto max-w-4xl bg-gray-50 dark:bg-neutral-900">
          <div className="bg-white dark:bg-neutral-900 border-b border-gray-200 dark:border-neutral-800 px-4 py-3 flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-400"></div>
              <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
              <div className="w-3 h-3 rounded-full bg-green-400"></div>
            </div>
            <div className="flex-1 text-center text-xs text-gray-400 font-mono">dashboard.use.net</div>
          </div>
          <img 
            src="https://picsum.photos/1200/800" 
            alt="Dashboard Preview" 
            className="w-full h-auto opacity-90 dark:opacity-80" 
          />
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 bg-white dark:bg-black transition-colors">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4 text-gray-900 dark:text-white">Our Key Features</h2>
            <p className="text-gray-500 dark:text-gray-400">Real residential proxies you have been looking for</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
            <div className="space-y-12">
               {[
                 { icon: Wifi, title: "Truly Residential Proxies", desc: "Proxies are hosted on residential computers, ensuring that they are the most trusted IPs to various anti-bot systems." },
                 { icon: Shield, title: "Ethical and Licensed", desc: "Our proxies are ethically sourced from various free VPNs, all fully licensed and compliant." },
                 { icon: Database, title: "No Logs", desc: "We do not log any of your traffic, and we do not store any of your data." }
               ].map((feat, i) => (
                 <div key={i} className="flex gap-4">
                   <div className="w-10 h-10 rounded-lg bg-gray-50 dark:bg-neutral-900 flex items-center justify-center flex-shrink-0 text-black dark:text-white">
                      <feat.icon size={20} strokeWidth={1.5} />
                   </div>
                   <div>
                     <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-white">{feat.title}</h3>
                     <p className="text-gray-500 dark:text-gray-400 leading-relaxed text-sm">{feat.desc}</p>
                   </div>
                 </div>
               ))}
            </div>
            <div className="flex justify-center">
               {/* Globe Placeholder */}
               <div className="w-80 h-80 rounded-full border border-gray-200 dark:border-neutral-800 relative flex items-center justify-center bg-gray-50 dark:bg-neutral-900">
                   <div className="absolute inset-0 border border-gray-100 dark:border-neutral-800 rounded-full animate-ping opacity-20"></div>
                   <Globe size={200} strokeWidth={0.5} className="text-gray-300 dark:text-neutral-700" />
               </div>
            </div>
          </div>
        </div>
      </section>

      {/* Statistics */}
      <section className="py-20 bg-gray-50 dark:bg-neutral-950 transition-colors">
        <div className="max-w-7xl mx-auto px-6 text-center">
           <h2 className="text-3xl font-bold mb-4 text-gray-900 dark:text-white">Statistics</h2>
           <p className="text-gray-500 dark:text-gray-400 mb-16">USE.NET is growing every day, and so is our proxy pool.</p>

           <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                { val: "1000+", label: "New U.S Proxies Daily" },
                { val: "102+", label: "Countries Covered" },
                { val: "50,000", label: "Daily Available Proxies" }
              ].map((stat, i) => (
                <div key={i} className="bg-white dark:bg-neutral-900 p-8 rounded-2xl shadow-sm border border-gray-100 dark:border-neutral-800">
                   <div className="text-5xl font-bold mb-2 text-black dark:text-white">{stat.val}</div>
                   <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">{stat.label}</div>
                </div>
              ))}
           </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-24 bg-white dark:bg-black transition-colors">
        <div className="max-w-7xl mx-auto px-6">
           <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4 text-gray-900 dark:text-white">Choose Your Proxy</h2>
            <p className="text-gray-500 dark:text-gray-400">We offer flexible pricing to suit your business needs.</p>
           </div>

           <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
             {/* Mobile */}
             <div className="p-8 rounded-2xl border border-gray-200 dark:border-neutral-800 hover:border-gray-300 dark:hover:border-neutral-700 transition-colors bg-white dark:bg-neutral-900">
                <div className="w-12 h-12 bg-gray-100 dark:bg-neutral-800 rounded-xl flex items-center justify-center mb-6 mx-auto text-black dark:text-white">
                   <Smartphone size={24} />
                </div>
                <h3 className="text-xl font-bold text-center mb-1 text-gray-900 dark:text-white">Mobile Proxy</h3>
                <p className="text-xs text-gray-500 dark:text-gray-400 text-center mb-6">For Anonymous Operations</p>
                <div className="text-center mb-8 text-gray-900 dark:text-white">
                   <span className="text-4xl font-bold">$1.5</span>
                   <span className="text-gray-500 dark:text-gray-400">/24 hours</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {["Unlimited Bandwidth", "4G/5G Mobile Network", "Carrier Diversity", "Unlimited Scaling"].map((f,i)=>(
                    <li key={i} className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-300">
                      <Check size={12} /> {f}
                    </li>
                  ))}
                </ul>
                <button onClick={() => navigate('/auth')} className="w-full bg-black dark:bg-white text-white dark:text-black py-3 rounded-lg text-sm font-medium hover:bg-gray-800 dark:hover:bg-gray-200 transition-colors">Get Started</button>
             </div>

             {/* Residential (Popular) */}
             <div className="p-8 rounded-2xl border border-black dark:border-white ring-1 ring-black dark:ring-white relative bg-white dark:bg-neutral-900 shadow-lg transform md:-translate-y-4 transition-colors">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-black dark:bg-white text-white dark:text-black text-xs font-bold px-3 py-1 rounded-full">
                  Most Popular
                </div>
                <div className="w-12 h-12 bg-gray-100 dark:bg-neutral-800 rounded-xl flex items-center justify-center mb-6 mx-auto text-black dark:text-white">
                   <Wifi size={24} />
                </div>
                <h3 className="text-xl font-bold text-center mb-1 text-gray-900 dark:text-white">Residential Proxy</h3>
                <p className="text-xs text-gray-500 dark:text-gray-400 text-center mb-6">For Real User Simulation</p>
                <div className="text-center mb-8 text-gray-900 dark:text-white">
                   <span className="text-4xl font-bold">$2.0</span>
                   <span className="text-gray-500 dark:text-gray-400">/24 hours</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {["Unlimited Bandwidth", "Highly Trusted", "Broad ISP Selection", "Suited For Any Task", "Lowest Bot And IP Fraud Score"].map((f,i)=>(
                    <li key={i} className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-300">
                      <Check size={12} /> {f}
                    </li>
                  ))}
                </ul>
                <button onClick={() => navigate('/auth')} className="w-full bg-black dark:bg-white text-white dark:text-black py-3 rounded-lg text-sm font-medium hover:bg-gray-800 dark:hover:bg-gray-200 transition-colors">Get Started</button>
             </div>

             {/* Hosting */}
             <div className="p-8 rounded-2xl border border-gray-200 dark:border-neutral-800 hover:border-gray-300 dark:hover:border-neutral-700 transition-colors bg-white dark:bg-neutral-900">
                <div className="w-12 h-12 bg-gray-100 dark:bg-neutral-800 rounded-xl flex items-center justify-center mb-6 mx-auto text-black dark:text-white">
                   <Server size={24} />
                </div>
                <h3 className="text-xl font-bold text-center mb-1 text-gray-900 dark:text-white">Hosting Proxy</h3>
                <p className="text-xs text-gray-500 dark:text-gray-400 text-center mb-6">For High Performance</p>
                <div className="text-center mb-8 text-gray-900 dark:text-white">
                   <span className="text-4xl font-bold">$0.5</span>
                   <span className="text-gray-500 dark:text-gray-400">/24 hours</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {["Unlimited Bandwidth", "For High Performance", "Fastest Output", "Highest Uptime"].map((f,i)=>(
                    <li key={i} className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-300">
                      <Check size={12} /> {f}
                    </li>
                  ))}
                </ul>
                <button onClick={() => navigate('/auth')} className="w-full bg-black dark:bg-white text-white dark:text-black py-3 rounded-lg text-sm font-medium hover:bg-gray-800 dark:hover:bg-gray-200 transition-colors">Get Started</button>
             </div>
           </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-24 bg-gray-50 dark:bg-neutral-950 transition-colors">
        <div className="max-w-3xl mx-auto px-6">
           <h2 className="text-3xl font-bold text-center mb-2 text-gray-900 dark:text-white">Your questions, answered</h2>
           <p className="text-center text-gray-500 dark:text-gray-400 mb-12">Answers to the most frequently asked questions</p>

           <div className="space-y-4">
             {FAQ_DATA.map((faq, i) => (
               <FaqAccordion key={i} item={faq} />
             ))}
           </div>
        </div>
      </section>

      <footer className="py-12 bg-white dark:bg-black text-center text-xs text-gray-400 dark:text-gray-600 border-t border-gray-100 dark:border-neutral-900 transition-colors">
        <p>&copy; 2024 USE.NET Inc. All rights reserved.</p>
      </footer>
    </div>
  );
};

const FaqAccordion: React.FC<{ item: FaqItem }> = ({ item }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="bg-white dark:bg-neutral-900 border border-gray-200 dark:border-neutral-800 rounded-lg overflow-hidden transition-colors">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-50 dark:hover:bg-neutral-800 transition-colors"
      >
        <span className="font-medium text-sm text-gray-900 dark:text-white">{item.question}</span>
        {isOpen ? <Minus size={16} className="text-gray-400" /> : <Plus size={16} className="text-gray-400" />}
      </button>
      {isOpen && (
        <div className="px-6 pb-4 text-sm text-gray-500 dark:text-gray-400">
          {item.answer}
        </div>
      )}
    </div>
  )
}

export default LandingPage;