# PostgreSQL Configuration
variable "postgres_version" {
  description = "PostgreSQL version to use"
  type        = string
  default     = "15-alpine"
}

variable "postgres_user" {
  description = "PostgreSQL username"
  type        = string
  default     = "datapulse"
}

variable "postgres_password" {
  description = "PostgreSQL password"
  type        = string
  default     = "ChangeMe2024!"
  sensitive   = true
}

variable "postgres_db" {
  description = "PostgreSQL database name"
  type        = string
  default     = "datapulse"
}

variable "postgres_port" {
  description = "PostgreSQL external port"
  type        = number
  default     = 5432
}

# FastAPI Configuration
variable "api_port" {
  description = "FastAPI external port"
  type        = number
  default     = 8000
}

# Prometheus Configuration
variable "prometheus_version" {
  description = "Prometheus version to use"
  type        = string
  default     = "latest"
}

variable "prometheus_port" {
  description = "Prometheus external port"
  type        = number
  default     = 9090
}

variable "prometheus_scrape_interval" {
  description = "Prometheus scrape interval"
  type        = string
  default     = "15s"
}

# Grafana Configuration
variable "grafana_version" {
  description = "Grafana version to use"
  type        = string
  default     = "latest"
}

variable "grafana_port" {
  description = "Grafana external port"
  type        = number
  default     = 3000
}

variable "grafana_admin_user" {
  description = "Grafana admin username"
  type        = string
  default     = "admin"
}

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  default     = "ChangeMe2024!"
  sensitive   = true
}

# Loki Configuration
variable "loki_version" {
  description = "Loki version to use"
  type        = string
  default     = "2.9.2"
}

variable "loki_port" {
  description = "Loki external port"
  type        = number
  default     = 3100
}

# Promtail Configuration
variable "promtail_version" {
  description = "Promtail version to use"
  type        = string
  default     = "2.9.2"
}

# AWS Configuration
variable "aws_region" {
  description = "AWS region for Secrets Manager"
  type        = string
  default     = "eu-west-1"
}

variable "aws_secret_name" {
  description = "AWS Secrets Manager secret name containing DB and Grafana credentials"
  type        = string
  default     = "datapulse/prod/credentials"
}

# Environment Configuration
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_1" {
  description = "CIDR block for public subnet 1"
  type        = string
  default     = "10.0.1.0/24"
}

variable "public_subnet_2" {
  description = "CIDR block for public subnet 2"
  type        = string
  default     = "10.0.2.0/24"
}

variable "private_subnet_1" {
  description = "CIDR block for private subnet 1"
  type        = string
  default     = "10.0.10.0/24"
}

variable "private_subnet_2" {
  description = "CIDR block for private subnet 2"
  type        = string
  default     = "10.0.11.0/24"
}

# ECS Configuration
variable "backend_cpu" {
  description = "CPU units for backend task (e.g., 256, 512, 1024)"
  type        = string
  default     = "512"
}

variable "backend_memory" {
  description = "Memory for backend task in MB (e.g., 512, 1024, 2048)"
  type        = string
  default     = "1024"
}

variable "backend_desired_count" {
  description = "Desired number of backend tasks"
  type        = number
  default     = 2
}

# Database Configuration for ECS
variable "database_host" {
  description = "Database host endpoint (RDS or existing)"
  type        = string
  default     = "datapulse-db.xxx.eu-west-1.rds.amazonaws.com"
}

variable "database_name" {
  description = "Database name"
  type        = string
  default     = "datapulse"
}

variable "database_password_secret" {
  description = "ARN of Secrets Manager secret containing database password"
  type        = string
  default     = "arn:aws:secretsmanager:eu-west-1:123456789012:secret:datapulse/db/password"
  sensitive   = true
}

# CloudWatch Logs
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

# EC2 Configuration
variable "ec2_public_key" {
  description = "EC2 public key for SSH access (or leave empty to auto-generate)"
  type        = string
  default     = ""
}

# SSH Key Generation
variable "generate_ssh_key" {
  description = "Whether to generate a new SSH key pair"
  type        = bool
  default     = true
}
