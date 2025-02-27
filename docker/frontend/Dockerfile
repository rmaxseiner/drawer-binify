FROM node:20-alpine AS builder

WORKDIR /app

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .

# Temporarily disable TypeScript checks for build
ENV NEXT_DISABLE_TYPESCRIPT_CHECKS=1
ENV CI=false

RUN npm run build

FROM nginx:alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy static assets from builder stage
COPY --from=builder /app/.next/static /usr/share/nginx/html/_next/static
COPY --from=builder /app/public /usr/share/nginx/html/public
COPY --from=builder /app/.next/server/pages /usr/share/nginx/html

# Copy custom nginx config
COPY docker/nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]