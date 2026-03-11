# =====================================================
# Automatic Secret Generation
# Creates and manages secrets in AWS Secrets Manager
# =====================================================

# Generate random password for PostgreSQL
resource "random_password" "postgres" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}|;:,.<>?"

  keepers = {
    # Regenerate on change
    environment = var.environment
  }
}

# Generate random password for Grafana
resource "random_password" "grafana" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}|;:,.<>?"

  keepers = {
    environment = var.environment
  }
}

# Generate random password for Redis auth
resource "random_password" "redis" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}|;:,.<>?"

  keepers = {
    environment = var.environment
  }
}

# Database Credentials Secret
resource "aws_secretsmanager_secret" "db_credentials" {
  name = "datapulse/${var.environment}/credentials"

  recovery_window_in_days = 7

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id

  secret_string = jsonencode({
    postgres_user          = var.postgres_user
    postgres_password      = var.postgres_password != null ? var.postgres_password : random_password.postgres.result
    postgres_db            = var.postgres_db
    grafana_admin_password = var.grafana_admin_password != null ? var.grafana_admin_password : random_password.grafana.result
  })
}

# Redis Credentials Secret
resource "aws_secretsmanager_secret" "redis_credentials" {
  name = "datapulse/${var.environment}/redis"

  recovery_window_in_days = 7

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

resource "aws_secretsmanager_secret_version" "redis_credentials" {
  secret_id = aws_secretsmanager_secret.redis_credentials.id

  secret_string = jsonencode({
    redis_auth_token = random_password.redis.result
    redis_endpoint   = aws_elasticache_replication_group.main.primary_endpoint_address
    redis_port       = aws_elasticache_replication_group.main.port
  })
}

# Application Secret Key
resource "random_password" "app_secret" {
  length  = 64
  special = false

  keepers = {
    environment = var.environment
  }
}

resource "aws_secretsmanager_secret" "app_secret" {
  name = "datapulse/${var.environment}/app-secret"

  recovery_window_in_days = 7

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

resource "aws_secretsmanager_secret_version" "app_secret" {
  secret_id = aws_secretsmanager_secret.app_secret.id

  secret_string = jsonencode({
    secret_key = random_password.app_secret.result
  })
}

# Update locals to use generated secrets
locals {
  # Use generated secrets (stored in Secrets Manager)
  db_secrets = {
    postgres_user          = var.postgres_user
    postgres_password      = var.postgres_password != null ? var.postgres_password : random_password.postgres.result
    postgres_db            = var.postgres_db
    grafana_admin_password = var.grafana_admin_password != null ? var.grafana_admin_password : random_password.grafana.result
  }

  postgres_user     = local.db_secrets.postgres_user
  postgres_password = local.db_secrets.postgres_password
  postgres_db       = local.db_secrets.postgres_db
  grafana_password  = local.db_secrets.grafana_admin_password
}

# Export secrets ARN for ECS tasks
output "db_credentials_secret_arn" {
  description = "ARN of the database credentials secret"
  value       = aws_secretsmanager_secret.db_credentials.arn
}

output "redis_credentials_secret_arn" {
  description = "ARN of the Redis credentials secret"
  value       = aws_secretsmanager_secret.redis_credentials.arn
}

output "app_secret_arn" {
  description = "ARN of the application secret"
  value       = aws_secretsmanager_secret.app_secret.arn
}
