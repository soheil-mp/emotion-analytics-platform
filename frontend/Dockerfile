# Build stage
FROM node:20.11-alpine3.19 AS build

# Set working directory
WORKDIR /app

# Copy package files and npm configuration first
COPY package.json package-lock.json .npmrc ./

# Install dependencies with comprehensive retry logic
RUN set -ex && \
    echo "Starting npm install with retry logic..." && \
    npm ci --no-audit --progress=false --loglevel=error || \
    (echo "Attempt 1 failed, waiting 10s..." && sleep 10 && \
     npm ci --no-audit --progress=false --loglevel=error) || \
    (echo "Attempt 2 failed, trying different registry..." && \
     npm config set registry https://registry.yarnpkg.com && \
     npm ci --no-audit --progress=false --loglevel=error) || \
    (echo "Attempt 3 failed, trying with cache clear..." && \
     npm cache clean --force && \
     npm ci --no-audit --progress=false --loglevel=error) || \
    (echo "Final attempt with simplified options..." && \
     npm install --production=false --no-audit --no-fund)

# Copy source code
COPY . ./

# Build the application with error handling
RUN set -ex && \
    echo "Building React application..." && \
    npm run build || \
    (echo "Build failed, checking for common issues..." && \
     echo "Node version:" && node --version && \
     echo "NPM version:" && npm --version && \
     echo "Available memory:" && free -h && \
     npm run build)

# Production stage
FROM nginx:alpine AS production

# Copy built assets from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Add custom nginx configuration for React SPA
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    \
    location /health { \
        access_log off; \
        return 200 "healthy\n"; \
        add_header Content-Type text/plain; \
    } \
    \
    gzip on; \
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript; \
}' > /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Run nginx
CMD ["nginx", "-g", "daemon off;"]

# Add health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
