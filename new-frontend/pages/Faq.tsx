import React, { useState } from 'react';
import { FaqItem } from '../types';
import { HelpCircle, Plus, Minus, MessageSquare, Mail } from 'lucide-react';

const FAQ_DATA: FaqItem[] = [
  { question: "How do I connect to a SOCKS5 proxy?", answer: "You can connect using any software that supports the SOCKS5 protocol. Copy the IP and Port from the dashboard and enter it into your software's proxy settings." },
  { question: "What is the difference between Residential and Mobile proxies?", answer: "Residential proxies are IP addresses assigned to real devices by ISPs. Mobile proxies are IPs assigned to mobile devices on 4G/5G networks. Mobile proxies often have higher trust scores but may rotate more frequently." },
  { question: "Are there logs?", answer: "No, we do not keep any logs of your activity. Your privacy is paramount to us." },
  { question: "What payment methods are accepted?", answer: "We accept major credit cards, PayPal, and various cryptocurrencies." },
  { question: "Are there any offers for bulk orders?", answer: "Yes, please contact our sales team for custom bulk pricing if you need more than 1000 proxies." },
  { question: "What are the refund policies?", answer: "We offer a 3-day money-back guarantee if the service does not meet your needs, provided bandwidth usage is under 100MB." },
  { question: "How do I top up my balance?", answer: "Click on the '+' icon next to your balance in the top right corner of the dashboard, or go to your profile menu and select 'Deposit Funds'." },
];

const Faq: React.FC = () => {
  return (
    <div className="min-h-full bg-gray-50 dark:bg-[#09090b] pb-20 transition-colors duration-200">
      <div className="max-w-4xl mx-auto px-6 pt-12">
        
        {/* Header */}
        <div className="text-center mb-12">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 mb-4">
                <HelpCircle size={24} />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">Frequently Asked Questions</h1>
            <p className="text-gray-500 dark:text-gray-400 max-w-xl mx-auto">
                Everything you need to know about USE.NET proxies and services. Can't find the answer you're looking for? Contact our support team.
            </p>
        </div>

        {/* FAQ List */}
        <div className="space-y-4 mb-16">
            {FAQ_DATA.map((faq, i) => (
                <FaqAccordion key={i} item={faq} />
            ))}
        </div>

        {/* Contact Support CTA */}
        <div className="bg-white dark:bg-[#18181b] border border-gray-200 dark:border-[#27272a] rounded-xl p-8 text-center shadow-sm transition-colors">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Still have questions?</h3>
            <p className="text-gray-500 dark:text-gray-400 mb-6">Our support team is available 24/7 to help you.</p>
            <div className="flex justify-center gap-4">
                <button className="px-6 py-2.5 bg-black dark:bg-white text-white dark:text-black rounded-lg font-medium hover:opacity-90 transition-opacity flex items-center gap-2">
                    <MessageSquare size={16} /> Live Chat
                </button>
                <button className="px-6 py-2.5 bg-gray-100 dark:bg-[#27272a] text-gray-900 dark:text-white border border-gray-200 dark:border-[#3f3f46] rounded-lg font-medium hover:bg-gray-200 dark:hover:bg-[#3f3f46] transition-colors flex items-center gap-2">
                    <Mail size={16} /> Email Support
                </button>
            </div>
        </div>

      </div>
    </div>
  );
};

const FaqAccordion: React.FC<{ item: FaqItem }> = ({ item }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="bg-white dark:bg-[#18181b] border border-gray-200 dark:border-[#27272a] rounded-xl overflow-hidden transition-colors hover:border-gray-300 dark:hover:border-gray-600">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-50 dark:hover:bg-[#27272a] transition-colors"
      >
        <span className="font-semibold text-gray-900 dark:text-white pr-4">{item.question}</span>
        {isOpen ? (
            <div className="bg-black dark:bg-white text-white dark:text-black rounded-full p-1 flex-shrink-0">
                <Minus size={12} />
            </div>
        ) : (
            <div className="bg-gray-100 dark:bg-[#27272a] text-gray-500 dark:text-gray-400 rounded-full p-1 flex-shrink-0">
                <Plus size={12} />
            </div>
        )}
      </button>
      <div 
        className={`px-6 overflow-hidden transition-all duration-300 ease-in-out ${
            isOpen ? 'max-h-96 pb-6 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <p className="text-gray-600 dark:text-gray-400 leading-relaxed text-sm">
          {item.answer}
        </p>
      </div>
    </div>
  )
}

export default Faq;