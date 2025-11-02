# Brother PT PWA - Standalone Progressive Web App
FROM nginx:alpine

# PWA Metadaten
LABEL name="Brother PT PWA" \
      version="1.0.0" \
      description="Progressive Web App für Brother PT-E550W Label Generator"

# PWA Files kopieren
COPY . /usr/share/nginx/html/

# Custom nginx config für PWA
COPY nginx.conf /etc/nginx/nginx.conf

# PWA-optimierte nginx config
RUN echo 'server { \
    listen 80; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    # PWA Hauptseite \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    \
    # Service Worker - keine Caches \
    location /sw.js { \
        add_header Cache-Control "no-cache, no-store, must-revalidate"; \
        expires epoch; \
    } \
    \
    # Manifest \
    location /manifest.json { \
        add_header Content-Type application/manifest+json; \
        expires 1d; \
    } \
    \
    # Static Assets caching \
    location ~* \.(js|css|png|ico|woff2?)$ { \
        expires 1y; \
        add_header Cache-Control "public, immutable"; \
    } \
    \
    # Gzip \
    gzip on; \
    gzip_vary on; \
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml; \
}' > /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

EXPOSE 80

# Nginx im Vordergrund starten
CMD ["nginx", "-g", "daemon off;"]