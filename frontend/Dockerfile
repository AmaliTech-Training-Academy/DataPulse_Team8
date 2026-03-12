FROM nginx:alpine

# Copy the DataPulse UI
COPY datapulse-ui.html /usr/share/nginx/html/index.html

# Copy custom nginx config for SPA routing and API proxying
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
