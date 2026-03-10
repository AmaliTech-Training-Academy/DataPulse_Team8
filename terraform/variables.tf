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
  default     = "datapulse123"
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
  default     = "admin123"
  sensitive   = true
}
