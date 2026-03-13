# =====================================================
# Amazon ElastiCache Redis
# =====================================================

# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name       = "datapulse-redis-subnet-group-${var.environment}"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  tags = {
    Name        = "datapulse-redis-subnet-group-${var.environment}"
    Environment = var.environment
  }
}

# ElastiCache Security Group
resource "aws_security_group" "elasticache" {
  name        = "datapulse-elasticache-${var.environment}"
  description = "Security group for ElastiCache Redis"
  vpc_id      = aws_vpc.main.id

  # Allow Redis from ECS tasks
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
    description     = "Redis from ECS tasks"
  }

  # Allow Redis from EC2 (for development)
  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "Redis from VPC"
  }

  # Allow all outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "datapulse-elasticache-sg-${var.environment}"
    Environment = var.environment
  }
}

# ElastiCache Redis Replication Group
resource "aws_elasticache_replication_group" "main" {
  replication_group_id = "datapulse-redis-${var.environment}"
  description          = "DataPulse Redis Cache"

  # Engine configuration
  engine         = "redis"
  engine_version = "7.0"
  # Node type - using t3.micro for budget optimization
  node_type          = "cache.t3.micro"
  num_cache_clusters = 1

  # Network configuration
  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.elasticache.id]

  # Storage and performance
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auto_minor_version_upgrade = true
  
  # MUST BE FALSE FOR SINGLE NODE (num_cache_clusters = 1)
  automatic_failover_enabled = false
  multi_az_enabled           = false

  # Log delivery
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_slow.name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "slow-log"
  }

  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_engine.name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "engine-log"
  }

  # Lifecycle
  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "datapulse-redis-${var.environment}"
    Environment = var.environment
    Project     = "DataPulse"
  }
}

# CloudWatch Log Groups for ElastiCache
resource "aws_cloudwatch_log_group" "redis_slow" {
  name              = "/aws/elasticache/datapulse/${var.environment}/slow-log"
  retention_in_days = var.environment == "prod" ? 7 : 1

  tags = {
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "redis_engine" {
  name              = "/aws/elasticache/datapulse/${var.environment}/engine-log"
  retention_in_days = var.environment == "prod" ? 7 : 1

  tags = {
    Environment = var.environment
  }
}

# ElastiCache Redis Outputs
output "redis_endpoint" {
  description = "Redis primary endpoint"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "redis_reader_endpoint" {
  description = "Redis reader endpoint"
  value       = aws_elasticache_replication_group.main.reader_endpoint_address
}

output "redis_port" {
  description = "Redis port"
  value       = aws_elasticache_replication_group.main.port
}

output "redis_auth_token" {
  description = "Redis auth token (if enabled)"
  value       = aws_elasticache_replication_group.main.transit_encryption_enabled ? aws_elasticache_replication_group.main.auth_token : ""
  sensitive   = true
}

output "redis_replication_group_id" {
  description = "Redis replication group ID"
  value       = aws_elasticache_replication_group.main.id
}
