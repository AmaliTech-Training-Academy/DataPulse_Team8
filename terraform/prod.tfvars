# ============================================================
# Production Variables - Use with terraform apply
# Example: terraform apply -var-file=prod.tfvars
# ============================================================

# AWS Region
aws_region = "us-east-1"

# Project & Environment
project_name = "datapulse"
environment  = "production"

# VPC Networking (keep defaults or customize)
# vpc_cidr            = "10.0.0.0/16"
# public_subnet_cidr_1 = "10.0.1.0/24"
# public_subnet_cidr_2 = "10.0.2.0/24"
# private_subnet_cidr_1 = "10.0.10.0/24"
# private_subnet_cidr_2 = "10.0.11.0/24"

# RDS PostgreSQL
db_instance_class     = "db.t3.micro"  # FREE tier eligible
db_allocated_storage  = 20              # 20GB - within free tier
db_max_allocated_storage = 100
postgres_user         = "datapulse"
postgres_password      = "CHANGE_ME_IN_PRODUCTION"
postgres_db            = "datapulse"

# ECS Fargate
ecs_cpu_backend       = "256"           # 0.25 vCPU
ecs_memory_backend    = "512"           # 512 MB
ecs_service_desired_count = 1

# API
api_port = 8000
