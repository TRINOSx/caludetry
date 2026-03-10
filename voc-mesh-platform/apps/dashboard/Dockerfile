# Stage 1: Build
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json ./
RUN npm install --frozen-lockfile || npm install

COPY . .
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:1.25-alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Add custom nginx config — serves under /agro/ path
COPY --from=build /app/dist /usr/share/nginx/html/agro

RUN cat > /etc/nginx/conf.d/default.conf <<'NGINX'
server {
    listen 80;
    server_name _;

    # gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript image/svg+xml;
    gzip_vary on;
    gzip_min_length 256;

    # Health check
    location /healthz {
        access_log off;
        return 200 "ok";
        add_header Content-Type text/plain;
    }

    # Dashboard under /agro/
    location /agro/ {
        alias /usr/share/nginx/html/agro/;
        try_files $uri $uri/ /agro/index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Redirect /agro to /agro/
    location = /agro {
        return 301 /agro/;
    }

    # Proxy API requests
    location /api/ {
        resolver 127.0.0.11 valid=30s ipv6=off;
        set $upstream_api http://api:8000;
        proxy_pass $upstream_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
NGINX

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
