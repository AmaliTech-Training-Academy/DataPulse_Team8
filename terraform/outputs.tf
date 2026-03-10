# PostgreSQL Outputs
output "postgres_url" {
  description = "PostgreSQL connection URL"
  value       = "postgresql://${var.postgres_user}:${var.postgres_password}@localhost:${var.postgres_port}/${var.postgres_db}"
  sensitive   = true
}

output "postgres_endpoint" {
  description = "PostgreSQL external endpoint"
  value       = "localhost:${var.postgres_port}"
}

# FastAPI Outputs
output "api_url" {
  description = "FastAPI base URL"
  value       = "http://localhost:${var.api_port}"
}

output "api_docs_url" {
  description = "FastAPI API documentation URL"
  value       = "http://localhost:${var.api_port}/docs"
}

output "api_health_url" {
  description = "FastAPI health check URL"
  value       = "http://localhost:${var.api_port}/health"
}

# Prometheus Outputs
output "prometheus_url" {
  description = "Prometheus UI URL"
  value       = "http://localhost:${var.prometheus_port}"
}

output "prometheus_scrape_target" {
  description = "Prometheus scrape target for FastAPI"
  value       = "http://datapulse-api:8000/metrics"
}

# Grafana Outputs
output "grafana_url" {
  description = "Grafana UI URL"
  value       = "http://localhost:${var.grafana_port}"
}

output "grafana_credentials" {
  description = "Grafana login credentials"
  value       = "Username: ${var.grafana_admin_user}, Password: ${var.grafana_admin_password}"
  sensitive   = true
}

# All Service URLs Summary
output "service_urls" {
  description = "All service URLs after deployment"
  value = {
    postgres   = "postgresql://localhost:${var.postgres_port}/${var.postgres_db}"
    api        = "http://localhost:${var.api_port}"
    api_docs   = "http://localhost:${var.api_port}/docs"
    prometheus = "http://localhost:${var.prometheus_port}"
    grafana    = "http://localhost:${var.grafana_port}"
  }
}
