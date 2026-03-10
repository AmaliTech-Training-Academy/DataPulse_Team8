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
