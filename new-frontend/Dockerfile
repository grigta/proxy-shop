# ============================================================================
# Multi-stage Dockerfile for Vite + React 19 Frontend
# ============================================================================
# This Dockerfile creates an optimized production build of the frontend
# using nginx to serve static files.
#
# Build with:
#   docker build \
#     --build-arg VITE_API_URL=https://api.proxy-shop.com \
#     --build-arg VITE_APP_URL=https://proxy-shop.com \
#     -t proxy-shop-frontend:latest .
#
# Run with:
#   docker run -p 80:80 proxy-shop-frontend:latest
# ============================================================================

# ============================================================================
# Stage 1: Build Stage
# ============================================================================
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies (including devDependencies for build)
RUN npm ci

# Copy all source files
COPY . .

# Build arguments for environment variables
ARG VITE_API_URL
ARG VITE_APP_URL
ARG VITE_ENABLE_DEBUG=false

# Set environment variables from build args
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_APP_URL=$VITE_APP_URL
ENV VITE_ENABLE_DEBUG=$VITE_ENABLE_DEBUG

# Build the application
# This creates optimized static files in /app/dist
RUN npm run build

# ============================================================================
# Stage 2: Production Stage with Nginx
# ============================================================================
FROM nginx:alpine

# Copy built files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Create custom nginx configuration for SPA routing
RUN echo 'server {' > /etc/nginx/conf.d/default.conf && \
    echo '    listen 80;' >> /etc/nginx/conf.d/default.conf && \
    echo '    server_name _;' >> /etc/nginx/conf.d/default.conf && \
    echo '' >> /etc/nginx/conf.d/default.conf && \
    echo '    root /usr/share/nginx/html;' >> /etc/nginx/conf.d/default.conf && \
    echo '    index index.html;' >> /etc/nginx/conf.d/default.conf && \
    echo '' >> /etc/nginx/conf.d/default.conf && \
    echo '    # Enable gzip compression' >> /etc/nginx/conf.d/default.conf && \
    echo '    gzip on;' >> /etc/nginx/conf.d/default.conf && \
    echo '    gzip_vary on;' >> /etc/nginx/conf.d/default.conf && \
    echo '    gzip_min_length 1024;' >> /etc/nginx/conf.d/default.conf && \
    echo '    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json application/xml+rss;' >> /etc/nginx/conf.d/default.conf && \
    echo '' >> /etc/nginx/conf.d/default.conf && \
    echo '    # Cache static assets' >> /etc/nginx/conf.d/default.conf && \
    echo '    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {' >> /etc/nginx/conf.d/default.conf && \
    echo '        expires 1y;' >> /etc/nginx/conf.d/default.conf && \
    echo '        add_header Cache-Control "public, immutable";' >> /etc/nginx/conf.d/default.conf && \
    echo '    }' >> /etc/nginx/conf.d/default.conf && \
    echo '' >> /etc/nginx/conf.d/default.conf && \
    echo '    # SPA routing - serve index.html for all routes' >> /etc/nginx/conf.d/default.conf && \
    echo '    location / {' >> /etc/nginx/conf.d/default.conf && \
    echo '        try_files $uri $uri/ /index.html;' >> /etc/nginx/conf.d/default.conf && \
    echo '    }' >> /etc/nginx/conf.d/default.conf && \
    echo '' >> /etc/nginx/conf.d/default.conf && \
    echo '    # Optional: Proxy API requests to backend (for production reverse proxy setup)' >> /etc/nginx/conf.d/default.conf && \
    echo '    # Uncomment if you want nginx to proxy backend API calls' >> /etc/nginx/conf.d/default.conf && \
    echo '    # location /api/ {' >> /etc/nginx/conf.d/default.conf && \
    echo '    #     proxy_pass http://backend:8000;' >> /etc/nginx/conf.d/default.conf && \
    echo '    #     proxy_set_header Host $host;' >> /etc/nginx/conf.d/default.conf && \
    echo '    #     proxy_set_header X-Real-IP $remote_addr;' >> /etc/nginx/conf.d/default.conf && \
    echo '    #     proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' >> /etc/nginx/conf.d/default.conf && \
    echo '    #     proxy_set_header X-Forwarded-Proto $scheme;' >> /etc/nginx/conf.d/default.conf && \
    echo '    # }' >> /etc/nginx/conf.d/default.conf && \
    echo '}' >> /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# ============================================================================
# Alternative: Development Dockerfile (hot reload)
# ============================================================================
# For development with hot module replacement, use this instead:
#
# FROM node:20-alpine
# WORKDIR /app
# COPY package*.json ./
# RUN npm ci
# COPY . .
# EXPOSE 3000
# CMD ["npm", "run", "dev", "--", "--host"]
# ============================================================================

# ============================================================================
# .dockerignore recommendations
# ============================================================================
# Create a .dockerignore file with the following content to optimize builds:
#
# node_modules/
# dist/
# .vite/
# .env
# .env.local
# .env.*.local
# .git/
# .gitignore
# README.md
# *.md
# .vscode/
# .idea/
# *.swp
# *.swo
# .DS_Store
# coverage/
# .nyc_output/
# ============================================================================

