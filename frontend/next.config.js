const createNextIntlPlugin = require('next-intl/plugin');

// Create next-intl plugin with i18n configuration
const withNextIntl = createNextIntlPlugin('./src/i18n.ts');

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable React strict mode for better error handling
  reactStrictMode: true,

  // Use SWC minifier for better performance
  swcMinify: true,

  // Image optimization configuration
  images: {
    domains: ['localhost', 'proxy-shop.com', 'penobsobdiveivw.xyz', '23.95.132.61'],
    formats: ['image/avif', 'image/webp']
  },

  // Public environment variables (accessible in browser)
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'
  },

  // Experimental features
  experimental: {
    // Enable Server Actions if needed
    serverActions: true
  }
};

// Export configuration with next-intl plugin
module.exports = withNextIntl(nextConfig);

