FROM python:3.11-slim

# Create non-root user
RUN groupadd -r datapulse && useradd -r -g datapulse datapulse

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/uploads && chown -R datapulse:datapulse /app
USER datapulse
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
