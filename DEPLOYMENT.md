# DataPulse Deployment Guide

This comprehensive guide provides complete instructions for setting up and running the DataPulse application from scratch. Follow these step-by-step instructions to get the full environment running without requiring prior knowledge of the project.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Environment Setup](#environment-setup)
4. [Understanding the Architecture](#understanding-the-architecture)
5. [Running the Application](#running-the-application)
6. [Verifying Services](#verifying-services)
7. [Terraform Setup (Cloud Deployment)](#terraform-setup-cloud-deployment)
8. [Running Tests](#running-tests)
9. [Access URLs and Credentials](#access-urls-and-credentials)
10. [Schema Documentation](#schema-documentation)
11. [Project Structure](#project-structure)
12. [Troubleshooting](#troubleshooting)
13. [Next Steps](#next-steps)

---

## Prerequisites

Before starting, ensure you have the following tools installed on your machine. Each tool serves a specific purpose in the development and deployment workflow.

### Required Tools

| Tool               | Version            | Purpose                                                                         | Installation Time |
| ------------------ | ------------------ | ------------------------------------------------------------------------------- | ----------------- |
| **Docker**         | 20.10+             | Container runtime for running all services (PostgreSQL, Backend, Grafana, etc.) | ~5 min            |
| **Docker Compose** | v2.0+              | Orchestrating multi-container applications                                      | ~2 min            |
| **Python**         | 3.11+              | Local development, running scripts, and test execution                          | ~3 min            |
| **Git**            | Any recent version | Version control for cloning and managing code                                   | ~2 min            |
| **Terraform**      | >= 1.0             | Cloud infrastructure provisioning (for AWS deployment)                          | ~5 min            |

### Detailed Installation Instructions

#### macOS Installation (Using Homebrew)

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Docker Desktop (includes Docker and Docker Compose)
# Download from: https://www.docker.com/products/docker-desktop
# Or install via Homebrew:
brew install --cask docker

# Install Python 3.11
brew install python@3.11

# Install Terraform
brew install terraform

# Install Git (usually pre-installed)
brew install git
```

#### Ubuntu/Debian Linux Installation

```bash
# Update package index
sudo apt-get update

# Install Docker
sudo apt-get install docker.io docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Install Python 3.11
sudo apt-get install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3.11-dev

# Install Terraform
sudo apt-get install wget unzip
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt-get update
sudo apt-get install terraform

# Install Git
sudo apt-get install git
```

#### Windows Installation (Using WSL2)

```bash
# 1. Install WSL2 (Windows Subsystem for Linux)
# Open PowerShell as Administrator and run:
wsl --install

# 2. Restart your computer

# 3. Open Ubuntu terminal and run:
sudo apt-get update
sudo apt-get install docker.io docker-compose python3.11 terraform git

# 4. Start Docker Desktop on Windows and configure:
sudo service docker start
```

#### Verifying Installations

After installation, verify all tools are working:

```bash
# Check Docker version
docker --version
# Expected output: Docker version 20.10.x or higher

# Check Docker Compose version
docker-compose --version
# Expected output: Docker Compose version v2.0.0 or higher

# Check Python version
python3 --version
# Expected output: Python 3.11.x

# Check Terraform version
terraform --version
# Expected output: Terraform v1.0.x or higher

# Check Git version
git --version
# Expected output: git version 2.x.x
```

---

## Quick Start

Get the application running in under 5 minutes with these simple commands. This quick start assumes you have all prerequisites installed.

```bash
# Step 1: Clone the repository
git clone https://github.com/your-org/DataPulse.git
cd DataPulse

# Step 2: Copy environment file (creates .env from .env.example)
cp .env.example .env

# Step 3: Start all services
# This builds and starts all containers: PostgreSQL, Backend API, PgAdmin, Prometheus, Grafana
docker-compose up --build

# Step 4: Wait for services to start (usually 1-2 minutes)
# You'll see logs streaming in the terminal
```

Once running, access the application at:

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## Environment Setup

### Step-by-Step Environment Configuration

#### Step 1: Understanding Environment Variables

The application uses environment variables for configuration. These variables are stored in the `.env` file and control database connections, passwords, and service settings.

#### Step 2: Copy the Example Environment File

```bash
# Copy .env.example to .env
cp .env.example .env
```

#### Step 3: Review and Customize Variables

Open the `.env` file in your preferred text editor:

```bash
# View the .env file
cat .env
```

The default configuration in `.env.example` contains:

```bash
# =============================================================
# DataPulse — Environment Variables
# DO NOT commit this file. It is listed in .gitignore.
# Copy .env.example to .env and fill in your values.
# =============================================================

# ── PostgreSQL ────────────────────────────────────────────────
POSTGRES_USER=datapulse
POSTGRES_PASSWORD=datapulse123
POSTGRES_DB=datapulse

# ── Service DB connection URLs (used inside Docker network) ──
DATABASE_URL=postgresql://datapulse:datapulse123@db:5432/datapulse
SOURCE_DB_URL=postgresql://datapulse:datapulse123@db:5432/datapulse
TARGET_DB_URL=postgresql://datapulse:datapulse123@db:5432/datapulse
AIRFLOW_DB_URL=postgresql+psycopg2://datapulse:datapulse123@db:5432/datapulse

# ── PgAdmin ───────────────────────────────────────────────────
PGADMIN_EMAIL=admin@datapulse.com
PGADMIN_PASSWORD=admin123

# ── Grafana ───────────────────────────────────────────────────
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin123

# ── Airflow ───────────────────────────────────────────────────
AIRFLOW_ADMIN_PASSWORD=admin

# ── Alerting (optional) ───────────────────────────────────────
DE_ALERT_EMAILS=
SLACK_WEBHOOK_URL=
```

#### Step 4: Important Security Notes

> ⚠️ **Security Warning**: The default passwords shown above are for local development only! Before deploying to any environment:
>
> 1. Change `POSTGRES_PASSWORD` to a strong, random password (minimum 16 characters)
> 2. Change `GRAFANA_ADMIN_PASSWORD` to a secure password
> 3. Change `PGADMIN_PASSWORD` to a secure password
> 4. If using AWS, store sensitive values in AWS Secrets Manager

---

## Understanding the Architecture

DataPulse is a multi-container application with the following components:

### Service Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DataPulse Architecture                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐  │
│   │   Backend    │────▶│  PostgreSQL  │◀────│   Pipeline   │  │
│   │   (FastAPI)  │     │   Database   │     │    (ETL)     │  │
│   └──────────────┘     └──────────────┘     └──────────────┘  │
│          │                                         │            │
│          ▼                                         ▼            │
│   ┌──────────────┐                         ┌──────────────┐   │
│   │     ALB      │                         │   Airflow    │   │
│   │  (External)  │                         │  (Optional)  │   │
│   └──────────────┘                         └──────────────┘   │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                   Monitoring Stack                      │   │
│   │  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │   │
│   │  │ Prometheus │─▶│  Grafana   │  │     Loki      │  │   │
│   │  │  (Metrics) │  │ (Dashboards)│  │   (Logs)     │  │   │
│   │  └────────────┘  └────────────┘  └────────────────┘  │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Descriptions

| Component      | Technology       | Purpose                                         | Default Port    |
| -------------- | ---------------- | ----------------------------------------------- | --------------- |
| **Backend**    | FastAPI (Python) | REST API for data validation and quality checks | 8000            |
| **Database**   | PostgreSQL 15    | Primary data store                              | 5432 (internal) |
| **Pipeline**   | Python (ETL)     | Extract, transform, and load quality metrics    | Internal        |
| **PgAdmin**    | PgAdmin 4        | PostgreSQL database management UI               | 5050            |
| **Prometheus** | Prometheus       | Metrics collection and monitoring               | 9090            |
| **Grafana**    | Grafana          | Visualization and dashboards                    | 3000            |
| **Loki**       | Grafana Loki     | Log aggregation                                 | 3100            |
| **Streamlit**  | Streamlit        | Data quality analytics dashboard                | 8501            |
| **Airflow**    | Apache Airflow   | Data pipeline orchestration (optional)          | 8088            |

---

## Running the Application

### Starting All Services

The main command to start the entire application stack:

```bash
# From the project root directory
docker-compose up --build
```

This command will:

1. Build Docker images for the backend and pipeline
2. Pull pre-built images for PostgreSQL, Grafana, Prometheus, etc.
3. Start all containers in the correct order
4. Set up networking between services
5. Initialize the database

### Starting Specific Services

You may not always need all services. Here are options for selective startup:

#### Database + Backend Only

```bash
# For API development without monitoring
docker-compose up db backend
```

#### With Monitoring Stack

```bash
# Include Prometheus and Grafana
docker-compose up db backend prometheus grafana
```

#### With Data Engineering (Airflow)

```bash
# Include Airflow for ETL pipelines
docker-compose --profile de up
```

#### Background Execution

To run services in the background (detached mode):

```bash
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Rebuilding Containers

When code changes are made, rebuild the affected services:

```bash
# Rebuild specific service
docker-compose build backend

# Rebuild all services
docker-compose build

# Full rebuild (no cache)
docker-compose build --no-cache
```

---

## Verifying Services

### Check Running Containers

```bash
# View running containers
docker-compose ps
```

Expected output:

```
NAME                IMAGE                  COMMAND                  SERVICE    CREATED   STATUS
datapulse-backend   datapulse-backend      "uvicorn app.main:ap…"   backend    ...       Up
datapulse-db       postgres:15.5-alpine   "docker-entrypoint.s…"   db         ...       Up (healthy)
datapulse-grafana  grafana/grafana:10.3   "/run.sh"                grafana    ...       Up
datapulse-pgadmin  dpage/pgadmin4:8.2     "/entrypoint.sh"         pgadmin    ...       Up
datapulse-prometheus prom/prometheus:v2.49 "/prometheus --config…" prometheus ...       Up
```

### Health Check Endpoints

Verify each service is responding:

```bash
# Backend API
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Prometheus
curl http://localhost:9090/-/healthy
# Expected: Prometheus is Healthy

# Grafana
curl http://localhost:3000/api/health
# Expected: {"database":"ok"}
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f db

# Last 100 lines
docker-compose logs --tail=100
```

---

## Terraform Setup (Cloud Deployment)

Deploy the application to AWS using Terraform. This creates a production-ready infrastructure with ECS Fargate, RDS PostgreSQL, ElastiCache Redis, and monitoring.

### Terraform Directory Structure

```
terraform/
├── main.tf           # Main configuration (providers, Docker resources)
├── variables.tf      # Input variables
├── outputs.tf        # Output values
├── ec2.tf            # EC2 instances
├── ecs.tf            # ECS cluster and services
├── rds.tf            # PostgreSQL database
├── elasticache.tf    # Redis cache
├── scheduler.tf      # Lambda cost optimizer
├── backend.tf        # Terraform backend config
├── secrets.tf        # Secrets management
├── ssm.tf            # Parameter Store
├── github_oidc.tf    # GitHub OIDC for CI/CD
├── task-definition.json  # ECS task definition
└── scripts/          # Deployment scripts
```

### Step 1: Navigate to Terraform Directory

```bash
cd terraform
```

### Step 2: Initialize Terraform

```bash
terraform init
```

This command:

- Downloads required providers (AWS, Docker, TLS, Random)
- Initializes the backend
- Creates the `.terraform` directory

Expected output:

```
Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan"
to see any changes that are required for your infrastructure.
```

### Step 3: Create Variable Files

Create a `dev.tfvars` file for development:

```bash
# Create dev.tfvars
cat > dev.tfvars << 'EOF'
# Environment
environment = "dev"
aws_region  = "eu-west-1"

# Database
postgres_user     = "datapulse"
postgres_password = "your-secure-dev-password"
postgres_db       = "datapulse"

# Grafana
grafana_admin_password = "your-grafana-password"

# EC2
generate_ssh_key = true

# ECS Configuration
backend_cpu           = "256"
backend_memory         = "512"
backend_desired_count  = 1
EOF
```

Create a `prod.tfvars` file for production:

```bash
# Create prod.tfvars
cat > prod.tfvars << 'EOF'
# Environment
environment = "prod"
aws_region  = "eu-west-1"

# Database
postgres_user     = "datapulse"
postgres_password = "your-secure-prod-password-minimum-16-chars"
postgres_db       = "datapulse"

# Grafana
grafana_admin_password = "your-secure-grafana-password"

# EC2
generate_ssh_key = true
ec2_public_key   = ""

# ECS Configuration
backend_cpu           = "512"
backend_memory         = "1024"
backend_desired_count  = 2
EOF
```

### Step 4: Review Infrastructure Plan

```bash
# Plan for development
terraform plan -var-file="dev.tfvars"

# Plan for production (shows all planned changes)
terraform plan -var-file="prod.tfvars"
```

Review the output carefully. It will show:

- Resources to be created
- Resources to be modified
- Resources to be destroyed

### Step 5: Apply Infrastructure

```bash
# Apply development environment
terraform apply -var-file="dev.tfvars"

# Apply production (requires yes/no approval)
terraform apply -var-file="prod.tfvars"
```

Type `yes` when prompted to confirm.

### Step 6: Get Deployment Outputs

After successful apply, get important values:

```bash
# Get ALB DNS name (service endpoint)
terraform output alb_dns_name

# Get ECS Cluster name
terraform output ecs_cluster_name

# Get Database endpoint
terraform output rds_endpoint

# Get all outputs
terraform output
```

### Step 7: Deploy Application

After infrastructure is ready, deploy the application:

```bash
# Using the deploy script
./deploy-to-ecr.sh

# Or manually build and push
docker build -t datapulse/backend:latest -f backend/Dockerfile ./backend
docker push your-account.dkr.ecr.eu-west-1.amazonaws.com/datapulse/backend:latest
```

### Step 8: Destroy Infrastructure (When Done)

```bash
# Destroy development environment
terraform destroy -var-file="dev.tfvars"

# Destroy production (requires yes/no)
terraform destroy -var-file="prod.tfvars"
```

> ⚠️ **Warning**: This will delete all data! Ensure you have backups if needed.

---

## Running Tests

### Option 1: Using Docker (Recommended)

This method runs tests in an isolated container with PostgreSQL:

```bash
# Run the full test suite
docker-compose -f docker-compose.test.yml up --build --exit-code-from api_test
```

This command:

1. Builds the test container
2. Starts a PostgreSQL database
3. Runs all tests
4. Reports results
5. Exits with appropriate code (0 = success, non-zero = failures)

### Option 2: Running Tests Locally

```bash
# Step 1: Create virtual environment
python3 -m venv .venv

# Step 2: Activate virtual environment
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate     # On Windows

# Step 3: Install dependencies
pip install -r backend/requirements.txt

# Step 4: Run tests
cd backend
pytest tests/ -v
```

### Option 3: Run Specific Test Files

```bash
# Test authentication
pytest backend/tests/test_auth.py -v

# Test rules API
pytest backend/tests/test_rules.py -v

# Test upload functionality
pytest backend/tests/test_upload.py -v

# Test reports
pytest backend/tests/test_reports.py -v

# Test integration
pytest backend/tests/test_integration.py -v

# Test end-to-end
pytest backend/tests/test_e2e.py -v
```

### Option 4: Run Tests with Coverage

```bash
# Install coverage package
pip install pytest-cov

# Run with coverage report
pytest backend/tests/ -v --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html  # On Mac
xdg-open htmlcov/index.html  # On Linux
```

### Understanding Test Results

Test output will show:

- **PASSED**: Test passed successfully
- **FAILED**: Test failed (check output for details)
- **SKIPPED**: Test was skipped (usually due to missing dependencies)
- **ERROR**: Test encountered an error (not just assertion failure)

---

## Access URLs and Credentials

### Local Development Environment

After running `docker-compose up`, the following services are available:

| Service                 | URL                         | Username            | Password | Purpose                             |
| ----------------------- | --------------------------- | ------------------- | -------- | ----------------------------------- |
| **Backend API**         | http://localhost:8000       | -                   | -        | REST API for data validation        |
| **API Documentation**   | http://localhost:8000/docs  | -                   | -        | OpenAPI/Swagger documentation       |
| **API ReDoc**           | http://localhost:8000/redoc | -                   | -        | Alternative API documentation       |
| **PgAdmin**             | http://localhost:5050       | admin@datapulse.com | admin123 | PostgreSQL database management      |
| **Grafana**             | http://localhost:3000       | admin               | admin123 | Dashboards and visualizations       |
| **Prometheus**          | http://localhost:9090       | -                   | -        | Metrics collection and querying     |
| **Streamlit Dashboard** | http://localhost:8501       | -                   | -        | Data quality analytics UI           |
| **Airflow Web UI**      | http://localhost:8088       | admin               | admin    | Pipeline orchestration (if enabled) |

### Production Environment (AWS)

After Terraform deployment, services are accessible via the Application Load Balancer:

```bash
# Get ALB DNS name
ALB_DNS=$(terraform output -raw alb_dns_name)
echo "Services available at: http://$ALB_DNS"
```

| Service               | Path                          | Authentication               |
| --------------------- | ----------------------------- | ---------------------------- |
| **Backend API**       | http://\<alb-dns\>/api        | None                         |
| **API Documentation** | http://\<alb-dns\>/docs       | None                         |
| **Grafana**           | http://\<alb-dns\>/grafana    | Configured in Terraform vars |
| **Prometheus**        | http://\<alb-dns\>/prometheus | None                         |

### Default Credentials Reference

| Service    | Default Username    | Default Password | Where to Change |
| ---------- | ------------------- | ---------------- | --------------- |
| PostgreSQL | datapulse           | datapulse123     | .env file       |
| PgAdmin    | admin@datapulse.com | admin123         | .env file       |
| Grafana    | admin               | admin123         | .env file       |
| Airflow    | admin               | admin            | .env file       |

---

## Schema Documentation

The DataPulse analytics schema is maintained by **Mubarak** and provides the foundation for all data quality reporting and analytics.

### Database Schema Overview

The analytics database consists of dimension and fact tables designed for efficient reporting:

#### Dimension Tables

| Table Name         | Purpose                        | Key Fields                                                         |
| ------------------ | ------------------------------ | ------------------------------------------------------------------ |
| **etl_batch_runs** | Tracks ETL pipeline executions | id, pipeline_name, status, started_at, finished_at                 |
| **dim_datasets**   | Source dataset metadata        | id, name, file_type, row_count, uploaded_by, status                |
| **dim_rules**      | Validation rule definitions    | id, name, rule_type, severity, field_name, parameters              |
| **dim_date**       | Calendar date dimension        | date_key, full_date, day_of_week, month, quarter, year, is_weekend |

#### Fact Tables

| Table Name              | Purpose                            | Key Fields                                                 |
| ----------------------- | ---------------------------------- | ---------------------------------------------------------- |
| **fact_quality_checks** | Individual rule validation results | dataset_id, rule_id, passed, failed_rows, failure_rate     |
| **fact_quality_scores** | Dataset-level quality scores       | dataset_id, score, total_rules, passed_rules, failed_rules |

### Analytics Views

Pre-built views for common reporting queries:

| View Name                    | Purpose               | Use Case                |
| ---------------------------- | --------------------- | ----------------------- |
| **vw_dataset_latest_score**  | Latest quality scores | Dashboard summary cards |
| **vw_daily_dataset_quality** | Daily quality trends  | Trend charts            |
| **vw_rule_failure_summary**  | Rule failure analysis | Issue identification    |

### Complete Schema Reference

For comprehensive documentation including:

- Complete column definitions with data types
- All constraints and indexes
- Source-to-target mappings
- Data quality rules
- Refresh and SLA contracts

See: **[DataPulse Analytics Schema and Data Dictionary](data-engineering/docs/analytics_schema_data_dictionary.md)**

---

## Project Structure

Understanding the project structure helps navigate the codebase:

```
DataPulse/
├── .github/
│   └── workflows/          # CI/CD pipelines
│       └── deploy.yml      # GitHub Actions deployment
├── .streamlit/             # Streamlit config
├── app/                   # Frontend (legacy)
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── config.py      # Configuration
│   │   ├── database.py    # Database connection
│   │   ├── main.py        # Application entry point
│   │   ├── middleware/    # HTTP middleware
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routers/       # API route handlers
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── utils/         # Utilities
│   ├── tests/             # Test suite
│   ├── Dockerfile
│   └── requirements.txt
├── data-engineering/      # ETL and analytics
│   ├── dashboards/        # Streamlit dashboards
│   ├── docs/             # Documentation
│   ├── pipeline/         # ETL pipeline code
│   ├── sample_data/      # Test data
│   ├── scripts/         # Utility scripts
│   └── sql/             # SQL schemas
├── devops/               # DevOps scripts
├── frontend/            # Frontend (nginx)
├── monitoring/          # Prometheus/Grafana configs
├── qa/                  # QA test data
├── terraform/           # Infrastructure as Code
│   ├── scripts/         # Deployment scripts
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── ec2.tf
│   ├── ecs.tf
│   ├── rds.tf
│   └── elasticache.tf
├── .env.example         # Environment template
├── docker-compose.yml   # Local development
├── docker-compose.test.yml  # Test environment
├── DEPLOYMENT.md        # This file
└── README.md            # Project overview
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Port already in use"

```bash
# Find what's using the port
lsof -i :8000  # For port 8000
lsof -i :5432  # For port 5432 (PostgreSQL)
lsof -i :3000  # For port 3000 (Grafana)

# Kill the process
kill <PID>

# Or use a different port in docker-compose.yml
```

#### Issue: "Database connection refused"

```bash
# Check if PostgreSQL is running
docker-compose ps db

# View database logs
docker-compose logs db

# Check health status
docker inspect datapulse-db | grep -A 10 Health

# Restart database
docker-compose restart db
```

#### Issue: "Container keeps restarting"

```bash
# View logs to find the error
docker-compose logs <service-name>

# Common causes:
# - Missing environment variables
# - Database not ready (add depends_on conditions)
# - Volume permissions

# Rebuild without cache
docker-compose build --no-cache <service-name>
```

#### Issue: "Permission denied" on Linux

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply new group (or logout/login)
newgrp docker

# Or run with sudo (not recommended for development)
sudo docker-compose up
```

#### Issue: Terraform state locked

```bash
# Check for lock
terraform force-unlock <lock-id>

# Or remove .terraform.lock.hcl and reinitialize
rm .terraform.lock.hcl
terraform init
```

#### Issue: AWS credentials not found

```bash
# Configure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=<your-key>
export AWS_SECRET_ACCESS_KEY=<your-secret>
export AWS_DEFAULT_REGION=eu-west-1
```

#### Issue: Tests failing

```bash
# Check test data exists
ls -la backend/tests/data/

# Run tests with verbose output
pytest backend/tests/ -v -s

# Run specific failing test
pytest backend/tests/test_auth.py::test_login -v
```

### Getting Help

If you encounter issues not covered here:

1. Check the logs: `docker-compose logs -f`
2. Check GitHub Issues: https://github.com/your-org/DataPulse/issues
3. Review CI/CD logs in GitHub Actions
4. Contact the team on Slack

---

## Next Steps

After getting the application running:

### For Developers

1. **Read the API Documentation**: Visit http://localhost:8000/docs
2. **Explore the Database**: Access PgAdmin at http://localhost:5050
3. **View Metrics**: Check Grafana at http://localhost:3000
4. **Run Test Suite**: Ensure all tests pass before making changes

### For Data Engineers

1. **Understand the ETL Pipeline**: Read data-engineering/pipeline/README.md
2. **Review Analytics Schema**: See data-engineering/docs/analytics_schema_data_dictionary.md
3. **Set up Airflow**: Run with `docker-compose --profile de up`

### For DevOps

1. **Review Terraform Code**: Explore the terraform/ directory
2. **Set up CI/CD**: Configure GitHub Actions secrets
3. **Plan Production Deployment**: Review DEPLOYMENT.md Terraform section

---

## Additional Resources

| Resource        | Description                   | Link                             |
| --------------- | ----------------------------- | -------------------------------- |
| Backend API     | Interactive API documentation | http://localhost:8000/docs       |
| PostgreSQL Docs | Database documentation        | https://www.postgresql.org/docs/ |
| FastAPI Docs    | Backend framework             | https://fastapi.tiangolo.com/    |
| Grafana Docs    | Visualization tool            | https://grafana.com/docs/        |
| Prometheus Docs | Monitoring system             | https://prometheus.io/docs/      |
| Terraform Docs  | Infrastructure as Code        | https://www.terraform.io/docs/   |
| Docker Docs     | Container platform            | https://docs.docker.com/         |

---

## Document Information

| Field             | Value          |
| ----------------- | -------------- |
| **Project**       | DataPulse      |
| **Version**       | 1.0.0          |
| **Last Updated**  | 2026-03-13     |
| **Maintained By** | DataPulse Team |
| **License**       | MIT            |

---

_This guide was created to help developers get up and running with DataPulse quickly. For questions or contributions, please open an issue on GitHub._
