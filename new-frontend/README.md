# Proxy Shop - Modern Web Frontend (Vite + React 19)

Modern, fast web interface for the proxy marketplace with seamless backend integration.

## 🎯 Project Overview

This is the new frontend for Proxy Shop, built with modern web technologies for optimal performance and developer experience. It provides a fast, responsive interface for users to manage proxy purchases, payments, and account settings.

### Tech Stack

- **Vite 6** - Lightning-fast build tool with hot module replacement
- **React 19** - Latest React with improved performance
- **TypeScript** - Full type safety
- **Tailwind CSS** - Utility-first styling
- **React Router DOM** - Client-side routing
- **Axios** - HTTP client with interceptors
- **lucide-react** - Beautiful icon library

### Key Features

- **Access Code Authentication** - Secure XXX-XXX-XXX format with server-side generation
- **SOCKS5/PPTP Proxy Catalog** - Real-time filtering by country, state, city, ZIP code
- **Purchase Flow** - Balance validation, coupon support, credential display
- **Purchase History** - Active/Expired filtering with extend/renew functionality
- **Heleket Payment Integration** - Universal crypto payments with automatic balance updates
- **Dark Mode** - Full theme support with ThemeContext
- **Multi-language Support** - English and Russian (via i18n)

## 📋 Prerequisites

- **Node.js 20+** required
- **Backend API** must be running (default: http://localhost:8000)
- **Environment variables** properly configured

## 🚀 Quick Start

### Installation

```bash
npm install
```

### Environment Setup

```bash
cp .env.example .env
# Edit .env and configure VITE_API_URL
```

### Development

```bash
npm run dev
```

Server runs on http://localhost:3000 with hot module replacement enabled.

### Production Build

```bash
npm run build
npm run preview
```

Built files will be in the `dist/` directory.

## 🔧 Environment Variables

| Variable | Description | Example (Dev) | Example (Prod) |
|----------|-------------|---------------|----------------|
| `VITE_API_URL` | Backend API base URL | `http://localhost:8000` | `https://api.proxy-shop.com` |
| `VITE_APP_URL` | Frontend base URL for referral links | `http://localhost:3000` | `https://proxy-shop.com` |
| `VITE_ENABLE_DEBUG` | Enable debug mode (optional) | `false` | `false` |

**Important Notes:**
- All client-side environment variables must have the `VITE_` prefix
- Backend secrets (JWT_SECRET_KEY, etc.) are NOT needed in the frontend
- Do not commit `.env` file to version control
- For Docker deployments, use Docker internal networking for services

## 📁 Project Structure

```
new-frontend/
├── pages/              # Main application pages
│   ├── Auth.tsx       # Registration and login
│   ├── Socks.tsx      # SOCKS5 proxy catalog
│   ├── Pptp.tsx       # PPTP proxy catalog
│   ├── History.tsx    # Purchase history
│   └── Landing.tsx    # Landing page
├── components/         # Reusable React components
│   └── Layout.tsx     # App layout with sidebar and header
├── lib/               # Core utilities
│   ├── api-client.ts  # Axios instance with interceptors
│   ├── constants.ts   # App constants
│   └── i18n.ts        # Internationalization setup
├── types/             # TypeScript type definitions
│   └── api.ts         # API response types
├── hooks/             # Custom React hooks
│   └── usePurchaseFlow.ts  # Purchase flow logic
├── AuthContext.tsx    # Authentication state provider
├── ThemeContext.tsx   # Theme state provider
├── App.tsx            # Root component
└── main.tsx           # Application entry point
```

## ✨ Features

### Authentication
- **Access Code Format:** XXX-XXX-XXX (11 characters, excludes I/O/0/1 for clarity)
- **Registration:** Codes generated server-side with cryptographically secure randomness
- **JWT Token Management:** Automatic token refresh with interceptors
- **Auto-login:** After registration, users are automatically logged in

### Proxy Catalog
- **Real-time Filtering:** Country, state, city, ZIP code
- **Pagination:** Server-side pagination with page controls
- **Speed Indicators:** Fast (green), Moderate (yellow), Slow (red)
- **Masked IPs:** Show XX.XX.*.* before purchase for security
- **Detailed Info:** ISP, organization, location data

### Purchase Flow
- **Balance Validation:** Client-side checks before purchase
- **Coupon Support:** Optional coupon codes for discounts
- **Confirmation Modal:** Review details before finalizing
- **Credential Display:** Full IP:Port:Login:Password after successful purchase
- **Copy to Clipboard:** One-click copy for all credentials

### History Management
- **Filtering:** Active, Expired, or All proxies
- **Search:** By IP address or country
- **Extend/Renew:** Add hours to active proxies or renew expired ones
- **Expiration Tracking:** Visual indicators for time remaining
- **Copy Credentials:** Quick access to proxy details

### Payment System
- **Heleket Integration:** Universal crypto payment links
- **Multi-currency:** User selects cryptocurrency on Heleket page
- **Automatic Updates:** Balance updated via webhooks
- **Transaction History:** View all payment transactions
- **Minimum Deposit:** $10 USD

## 🛠 Development

### Hot Module Replacement
Vite provides instant hot module replacement for rapid development:
- Changes reflect immediately without full page reload
- React state is preserved during updates
- Fast feedback loop for UI development

### TypeScript
Full TypeScript support with strict mode enabled:
- Type-safe API calls
- IntelliSense support
- Compile-time error detection

### Dark Mode
Theme toggle via ThemeContext:
- Persisted in localStorage
- Instant theme switching
- All components theme-aware

### API Client
Centralized API client with automatic features:
- Token refresh interceptors
- Error handling
- Request/response logging (debug mode)
- Base URL configuration

## 🐳 Docker Deployment

The frontend is integrated into the main Docker Compose setup.

**Service Name:** `new-frontend`

**Port:** 3000

**Environment Variables:** Passed from root `.env` file

**Reference:** See `docker-compose.yml` in project root

**Development Mode:**
```bash
docker-compose up -d new-frontend
```

**Production Build:** Use the included `Dockerfile` for optimized nginx-served static files.

## 🔌 API Integration

### Endpoints Used

**Authentication:**
- `POST /api/auth/register` - Create new user
- `POST /api/auth/login` - Login with access code
- `POST /api/auth/verify` - Verify JWT token
- `POST /api/auth/refresh` - Refresh access token

**Products:**
- `GET /api/products/socks5` - SOCKS5 catalog with filters
- `GET /api/products/pptp` - PPTP catalog with filters
- `GET /api/products/countries` - Available countries

**Purchase:**
- `POST /api/purchase/socks5` - Purchase SOCKS5 proxy
- `POST /api/purchase/pptp` - Purchase PPTP proxy
- `GET /api/purchase/history/{userId}` - Purchase history
- `POST /api/purchase/extend/{proxyId}` - Extend proxy duration

**Payment:**
- `POST /api/payment/generate-address` - Create Heleket invoice
- `GET /api/payment/history/{userId}` - Payment transaction history

**User:**
- `GET /api/user/profile` - User profile and balance

### API Client Location
- **Implementation:** `src/lib/api-client.ts`
- **Type Definitions:** `src/types/api.ts`
- **Usage:** Import `apiClient` and call methods with full TypeScript support

## 🐛 Troubleshooting

### Common Issues

**"Network Error"**
- Check `VITE_API_URL` in `.env`
- Verify backend is running: `http://localhost:8000/api/docs`
- Check CORS configuration in backend

**"401 Unauthorized"**
- Clear localStorage: `localStorage.clear()`
- Re-login with valid access code
- Check token expiration settings

**Build Errors**
- Delete `node_modules`: `rm -rf node_modules`
- Clear npm cache: `npm cache clean --force`
- Reinstall: `npm install`

**Port 3000 Already in Use**
- Change port in `vite.config.ts`:
  ```ts
  server: {
    port: 3001 // or any other port
  }
  ```

**Hot Reload Not Working**
- Check file watchers limit (Linux): `echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf`
- Restart Vite dev server

## 🤝 Contributing

### Code Style
- Follow existing patterns and conventions
- Use TypeScript for all new code
- Format with Prettier (if configured)
- Use meaningful variable and function names

### TypeScript
- All new code must be fully typed
- Avoid `any` type - use proper types or `unknown`
- Export types for reusability

### Testing
- Manual testing checklist in root `README.md`
- Test all user flows before committing
- Verify responsive design on multiple screen sizes

## 📄 License

Proprietary software. All rights reserved.

## 📞 Support

For issues and questions, contact the development team or refer to the main project documentation.

---

**Note:** This frontend replaces the old Next.js frontend. For migration notes and rollback procedures, see the main `README.md` in the project root.
