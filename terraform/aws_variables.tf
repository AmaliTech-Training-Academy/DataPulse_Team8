# ============================================================
# AWS Variables for ECS/ECR Deployment
# ============================================================

# AWS Region
variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

# Project Name (used for resource naming)
variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "datapulse"
}

# Environment
variable "environment" {
  description = "Environment (development, staging, production)"
  type        = string
  default     = "development"
}

# ============================================================
# VPC Networking
# ============================================================
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr_1" {
  description = "Public subnet 1 CIDR"
  type        = string
  default     = "10.0.1.0/24"
}

variable "public_subnet_cidr_2" {
  description = "Public subnet 2 CIDR"
  type        = string
  default     = "10.0.2.0/24"
}

variable "private_subnet_cidr_1" {
  description = "Private subnet 1 CIDR"
  type        = string
  default     = "10.0.10.0/24"
}

variable "private_subnet_cidr_2" {
  description = "Private subnet 2 CIDR"
  type        = string
  default     = "10.0.11.0/24"
}

# ============================================================
# RDS PostgreSQL Configuration
# ============================================================
variable "db_instance_class" {
  description = "RDS instance class (db.t3.micro for free tier, db.t3.small for better performance)"
  type        = string
  default     = "db.t3.micro" # FREE tier eligible
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20 # 20GB - within free tier
}

variable "db_max_allocated_storage" {
  description = "RDS maximum allocated storage in GB"
  type        = number
  default     = 100
}

# Keep existing PostgreSQL variables
variable "postgres_version" {
  description = "PostgreSQL version to use"
  type        = string
  default     = "15.4"
}

variable "postgres_user" {
  description = "PostgreSQL username"
  type        = string
  default     = "datapulse"
}

variable "postgres_password" {
  description = "PostgreSQL password"
  type        = string
  default     = "datapulse123"
  sensitive   = true
}

variable "postgres_db" {
  description = "PostgreSQL database name"
  type        = string
  default     = "datapulse"
}

# ============================================================
# ECS Fargate Configuration
# ============================================================
variable "ecs_cpu_backend" {
  description = "ECS CPU units for backend (256 = 0.25 vCPU)"
  type        = string
  default     = "256"
}

variable "ecs_memory_backend" {
  description = "ECS memory in MB for backend (512 MB)"
  type        = string
  default     = "512"
}

variable "ecs_service_desired_count" {
  description = "Number of ECS tasks to run"
  type        = number
  default     = 1
}

# ============================================================
# FastAPI Configuration
# ============================================================
variable "api_port" {
  description = "FastAPI container port"
  type        = number
  default     = 8000
}
