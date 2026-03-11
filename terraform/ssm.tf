# =====================================================
# AWS Systems Manager Parameter Store
# Configuration parameters for the application
# =====================================================

# Application Parameters
resource "aws_ssm_parameter" "app_env" {
  name  = "/datapulse/${var.environment}/app/env"
  type  = "String"
  value = var.environment

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

resource "aws_ssm_parameter" "app_region" {
  name  = "/datapulse/${var.environment}/app/region"
  type  = "String"
  value = var.aws_region

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

# Database Parameters
resource "aws_ssm_parameter" "db_host" {
  name  = "/datapulse/${var.environment}/database/host"
  type  = "String"
  value = aws_db_instance.main.endpoint

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

resource "aws_ssm_parameter" "db_name" {
  name  = "/datapulse/${var.environment}/database/name"
  type  = "String"
  value = var.database_name

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

resource "aws_ssm_parameter" "db_port" {
  name  = "/datapulse/${var.environment}/database/port"
  type  = "String"
  value = "5432"

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

# Redis Parameters
resource "aws_ssm_parameter" "redis_endpoint" {
  name  = "/datapulse/${var.environment}/redis/endpoint"
  type  = "String"
  value = aws_elasticache_replication_group.main.primary_endpoint_address

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

resource "aws_ssm_parameter" "redis_port" {
  name  = "/datapulse/${var.environment}/redis/port"
  type  = "String"
  value = "6379"

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

# ECS Parameters
resource "aws_ssm_parameter" "ecs_cluster" {
  name  = "/datapulse/${var.environment}/ecs/cluster"
  type  = "String"
  value = aws_ecs_cluster.main.name

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

resource "aws_ssm_parameter" "ecs_service" {
  name  = "/datapulse/${var.environment}/ecs/service"
  type  = "String"
  value = aws_ecs_service.backend_blue.name

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

# ALB Parameters
resource "aws_ssm_parameter" "alb_dns" {
  name  = "/datapulse/${var.environment}/alb/dns"
  type  = "String"
  value = aws_lb.main.dns_name

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

# Secrets ARNs (SecureString)
resource "aws_ssm_parameter" "db_credentials_arn" {
  name      = "/datapulse/${var.environment}/secrets/db-arn"
  type      = "String"
  value     = aws_secretsmanager_secret.db_credentials.arn
  overwrite = true

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

resource "aws_ssm_parameter" "app_secret_arn" {
  name      = "/datapulse/${var.environment}/secrets/app-arn"
  type      = "String"
  value     = aws_secretsmanager_secret.app_secret.arn
  overwrite = true

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

# API Configuration
resource "aws_ssm_parameter" "api_port" {
  name  = "/datapulse/${var.environment}/api/port"
  type  = "String"
  value = "8000"

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

# Monitoring Configuration
resource "aws_ssm_parameter" "prometheus_url" {
  name  = "/datapulse/${var.environment}/monitoring/prometheus-url"
  type  = "String"
  value = "http://localhost:9090"

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

resource "aws_ssm_parameter" "grafana_url" {
  name  = "/datapulse/${var.environment}/monitoring/grafana-url"
  type  = "String"
  value = "http://localhost:3000"

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

# SSM Parameter Outputs
output "ssm_parameter_names" {
  description = "List of SSM parameter names created"
  value = [
    aws_ssm_parameter.app_env.name,
    aws_ssm_parameter.app_region.name,
    aws_ssm_parameter.db_host.name,
    aws_ssm_parameter.db_name.name,
    aws_ssm_parameter.db_port.name,
    aws_ssm_parameter.redis_endpoint.name,
    aws_ssm_parameter.redis_port.name,
    aws_ssm_parameter.ecs_cluster.name,
    aws_ssm_parameter.ecs_service.name,
    aws_ssm_parameter.alb_dns.name,
    aws_ssm_parameter.db_credentials_arn.name,
    aws_ssm_parameter.app_secret_arn.name,
    aws_ssm_parameter.api_port.name,
    aws_ssm_parameter.prometheus_url.name,
    aws_ssm_parameter.grafana_url.name,
  ]
}
