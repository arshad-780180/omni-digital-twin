# ──────────────────────────────────────────────────────────────────────────────
# OMNI Digital Twin — Frontend Dockerfile
# Production-ready Multi-stage build with Nginx
# ──────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

# Metadata
LABEL maintainer="OMNI Digital Twin"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Copy package files for dependency installation
# This leverages Docker cache to avoid re-installing dependencies if package.json hasn't changed
COPY package.json package-lock.json ./
RUN npm ci

# Copy the rest of the application code
COPY . .

# Set build arguments for environment variables
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Build the React/Vite application for production
RUN npm run build

# ── Stage 2: Serve ────────────────────────────────────────────────────────────
FROM nginx:alpine

# Remove default Nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built assets from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Add a custom Nginx configuration for single-page applications (SPA) routing
# We will create a simple config that falls back to index.html for React Router
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
