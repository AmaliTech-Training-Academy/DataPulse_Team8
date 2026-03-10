terraform {
  required_version = ">= 1.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "3.0.2"
    }
  }
}

provider "docker" {
  host = "unix:///var/run/docker.sock"
}

# Internal Docker network for secure container communication
resource "docker_network" "datapulse_net" {
  name     = "datapulse_internal"
  internal = true
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

  # No external port - only accessible via internal Docker network
  # API connects via: datapulse-db:5432

  volumes {
    volume_name    = "datapulse_postgres_data"
    container_path = "/var/lib/postgresql/data"
  }

  networks_advanced {
    name = docker_network.datapulse_net.name
  }

  memory     = 512
  cpu_shares = 512
  restart    = "unless-stopped"
  read_only  = true

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

  # Public API - bound to 0.0.0.0 for external access
  ports {
    internal = 8000
    external = var.api_port
    ip       = "0.0.0.0"
  }

  networks_advanced {
    name = docker_network.datapulse_net.name
  }

  memory     = 512
  cpu_shares = 512
  restart    = "unless-stopped"
  read_only  = true
  tmpfs      = { "/tmp" = "rw,noexec,nosuid,size=100m" }

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

  # Internal only - localhost access
  ports {
    internal = 9090
    external = var.prometheus_port
    ip       = "127.0.0.1"
  }

  volumes {
    host_path      = pathexpand("~/Amalitech/DataPulse_Team8/terraform/prometheus.yml")
    container_path = "/etc/prometheus/prometheus.yml"
  }

  volumes {
    volume_name    = "datapulse_prometheus_data"
    container_path = "/prometheus"
  }

  networks_advanced {
    name = docker_network.datapulse_net.name
  }

  memory     = 512
  cpu_shares = 512
  restart    = "unless-stopped"
  read_only  = true
  tmpfs      = { "/tmp" = "rw,noexec,nosuid,size=100m" }
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

  # Internal only - localhost access
  ports {
    internal = 3000
    external = var.grafana_port
    ip       = "127.0.0.1"
  }

  volumes {
    volume_name    = "datapulse_grafana_data"
    container_path = "/var/lib/grafana"
  }

  volumes {
    volume_name    = "datapulse_grafana_provisioning"
    container_path = "/etc/grafana/provisioning"
  }

  networks_advanced {
    name = docker_network.datapulse_net.name
  }

  memory     = 256
  cpu_shares = 256
  restart    = "unless-stopped"
  read_only  = true
  tmpfs      = { "/tmp" = "rw,noexec,nosuid,size=50m" }

  depends_on = [docker_container.loki]
}

# Loki (Log Aggregator)
resource "docker_image" "loki" {
  name         = "grafana/loki:${var.loki_version}"
  keep_locally = true
}

resource "docker_container" "loki" {
  name  = "datapulse-loki"
  image = docker_image.loki.image_id

  command = [
    "-config.file=/etc/loki/loki-config.yml"
  ]

  # Internal only - localhost access
  ports {
    internal = 3100
    external = var.loki_port
    ip       = "127.0.0.1"
  }

  volumes {
    host_path      = pathexpand("~/Amalitech/DataPulse_Team8/monitoring/loki-config.yml")
    container_path = "/etc/loki/loki-config.yml"
  }

  volumes {
    volume_name    = "datapulse_loki_data"
    container_path = "/tmp/loki"
  }

  networks_advanced {
    name = docker_network.datapulse_net.name
  }

  memory     = 256
  cpu_shares = 256
  restart    = "unless-stopped"
  read_only  = true
  tmpfs      = { "/tmp" = "rw,noexec,nosuid,size=50m" }
}

# Promtail (Log Shipper)
resource "docker_image" "promtail" {
  name         = "grafana/promtail:${var.promtail_version}"
  keep_locally = true
}

resource "docker_container" "promtail" {
  name  = "datapulse-promtail"
  image = docker_image.promtail.image_id

  command = [
    "-config.file=/etc/promtail/promtail-config.yml"
  ]

  volumes {
    host_path      = "/var/lib/docker/containers"
    container_path = "/var/lib/docker/containers"
    read_only      = true
  }

  volumes {
    host_path      = pathexpand("~/Amalitech/DataPulse_Team8/monitoring/promtail-config.yml")
    container_path = "/etc/promtail/promtail-config.yml"
  }

  networks_advanced {
    name = docker_network.datapulse_net.name
  }

  memory     = 128
  cpu_shares = 128
  restart    = "unless-stopped"
  read_only  = true

  depends_on = [docker_container.loki]
}
