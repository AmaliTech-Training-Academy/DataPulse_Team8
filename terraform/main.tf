terraform {
  required_version = ">= 1.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {
  host = "unix:///var/run/docker.sock"
}

# PostgreSQL Database
resource "docker_image" "postgres" {
  name         = "postgres:${var.postgres_version}"
  keep_locally = true
}

resource "docker_container" "postgres" {
  name  = "datapulse-db"
  image = docker_image.postgres.image_id

  env = [
    "POSTGRES_USER=${var.postgres_user}",
    "POSTGRES_PASSWORD=${var.postgres_password}",
    "POSTGRES_DB=${var.postgres_db}"
  ]

  ports {
    internal = 5432
    external = var.postgres_port
  }

  volumes {
    volume_name    = "datapulse_postgres_data"
    container_path = "/var/lib/postgresql/data"
  }

  healthcheck {
    test     = ["CMD-SHELL", "pg_isready -U ${var.postgres_user}"]
    interval = "10s"
    timeout  = "5s"
    retries  = 5
  }
}

# FastAPI Backend
resource "docker_image" "fastapi" {
  name = "datapulse-backend:latest"
  build {
    context    = pathexpand("~/Amalitech/DataPulse_Team8/backend")
    dockerfile = "Dockerfile"
  }
  keep_locally = true
}

resource "docker_container" "fastapi" {
  name  = "datapulse-api"
  image = docker_image.fastapi.image_id

  env = [
    "DATABASE_URL=postgresql://${var.postgres_user}:${var.postgres_password}@datapulse-db:5432/${var.postgres_db}"
  ]

  ports {
    internal = 8000
    external = var.api_port
  }

  depends_on = [docker_container.postgres]

  healthcheck {
    test     = ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval = "30s"
    timeout  = "10s"
    retries  = 3
  }
}

# Prometheus
resource "docker_image" "prometheus" {
  name         = "prometheus:${var.prometheus_version}"
  keep_locally = true
}

resource "docker_container" "prometheus" {
  name  = "datapulse-prometheus"
  image = docker_image.prometheus.image_id

  command = [
    "--config.file=/etc/prometheus/prometheus.yml",
    "--storage.tsdb.path=/prometheus",
    "--web.console.libraries=/usr/share/prometheus/console_libraries",
    "--web.console.templates=/usr/share/prometheus/consoles"
  ]

  ports {
    internal = 9090
    external = var.prometheus_port
  }

  volumes {
    host_path      = pathexpand("~/Amalitech/DataPulse_Team8/terraform/prometheus.yml")
    container_path = "/etc/prometheus/prometheus.yml"
  }

  volumes {
    volume_name    = "datapulse_prometheus_data"
    container_path = "/prometheus"
  }
}

# Grafana
resource "docker_image" "grafana" {
  name         = "grafana:${var.grafana_version}"
  keep_locally = true
}

resource "docker_container" "grafana" {
  name  = "datapulse-grafana"
  image = docker_image.grafana.image_id

  env = [
    "GF_SECURITY_ADMIN_USER=${var.grafana_admin_user}",
    "GF_SECURITY_ADMIN_PASSWORD=${var.grafana_admin_password}"
  ]

  ports {
    internal = 3000
    external = var.grafana_port
  }

  volumes {
    volume_name    = "datapulse_grafana_data"
    container_path = "/var/lib/grafana"
  }

  volumes {
    volume_name    = "datapulse_grafana_provisioning"
    container_path = "/etc/grafana/provisioning"
  }
}
