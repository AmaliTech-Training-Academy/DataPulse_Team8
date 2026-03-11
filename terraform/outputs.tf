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

# =====================================================
# ECS/ECR Outputs (Cloud)
# =====================================================

# ECR Repository URLs
output "ecr_backend_url" {
  description = "ECR repository URL for backend"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_frontend_url" {
  description = "ECR repository URL for frontend"
  value       = aws_ecr_repository.frontend.repository_url
}

# ECS Cluster
output "ecs_cluster_name" {
  description = "ECS Cluster name"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ECS Cluster ARN"
  value       = aws_ecs_cluster.main.arn
}

# Application Load Balancer
output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.main.dns_name
}

output "alb_arn" {
  description = "ALB ARN"
  value       = aws_lb.main.arn
}

# CodeDeploy
output "codedeploy_app_name" {
  description = "CodeDeploy application name"
  value       = aws_codedeploy_app.backend.name
}

output "codedeploy_deployment_group" {
  description = "CodeDeploy deployment group name"
  value       = aws_codedeploy_deployment_group.backend.deployment_group_name
}

# VPC
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = [aws_subnet.private_1.id, aws_subnet.private_2.id]
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = [aws_subnet.public_1.id, aws_subnet.public_2.id]
}

# =====================================================
# GitHub OIDC Outputs (already defined in github_oidc.tf)
# =====================================================

output "github_actions_deploy_role_arn" {
  description = "ARN of the IAM role for GitHub Actions deployment - add this as GITHUB_OIDC_ROLE_ARN secret"
  value       = aws_iam_role.github_actions_deploy.arn
}

output "github_actions_deploy_role_name" {
  description = "Name of the IAM role for GitHub Actions deployment"
  value       = aws_iam_role.github_actions_deploy.name
}
