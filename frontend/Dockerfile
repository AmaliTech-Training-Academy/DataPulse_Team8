FROM nginx:1.25.3-alpine

# Create a non-root user and setup directories
RUN mkdir -p /var/cache/nginx /var/run /var/log/nginx && \
    chown -R nginx:nginx /var/cache/nginx /var/run /var/log/nginx

# Copy the DataPulse UI and set ownership
COPY --chown=nginx:nginx datapulse-ui.html /usr/share/nginx/html/index.html

# Copy custom nginx config
COPY --chown=nginx:nginx nginx.conf /etc/nginx/conf.d/default.conf

# Switch to non-root user
USER nginx

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://localhost:8080/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
