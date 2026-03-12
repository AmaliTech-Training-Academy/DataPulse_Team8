# DataPulse DevOps Documentation

This document provides comprehensive documentation of the DevOps infrastructure, CI/CD pipelines, challenges encountered, and commands used in the DataPulse project. This includes all aspects from local development setup to production deployment on AWS.

## Table of Contents

1. [Overview](#overview)
2. [DevOps Folder Structure](#devops-folder-structure)
3. [Infrastructure Components](#infrastructure-components)
4. [CI/CD Pipelines](#cicd-pipelines)
5. [Challenges and Solutions](#challenges-and-solutions)
6. [Commands Reference](#commands-reference)
7. [Environment Variables](#environment-variables)
8. [Deployment Workflows](#deployment-workflows)
9. [Local Development Setup](#local-development-setup)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)

---

## Overview

The DataPulse project uses a modern DevOps approach with multiple AWS services and tools to ensure reliable, scalable, and secure deployments. The infrastructure is designed to support both development and production environments with automated CI/CD pipelines.

The project includes:

- Infrastructure as Code (IaC): Terraform for AWS resource provisioning
- Container Orchestration: Amazon ECS with Fargate for serverless container management
- CI/CD: GitHub Actions with OIDC authentication for secure, credential-less deployments
- Container Registry: Amazon ECR for storing and managing Docker images
- Blue-Green Deployment: AWS CodeDeploy with Application Load Balancer for zero-downtime deployments
- Secrets Management: AWS Secrets Manager and Systems Manager Parameter Store for secure credential storage
- Monitoring: Prometheus for metrics collection, Grafana for visualization, and Loki for log aggregation

---

## DevOps Folder Structure

The devops folder contains all the necessary scripts, Docker configurations, and deployment workflows for the DataPulse project.

```
devops/
├── Dockerfile.pipeline          # Docker image definition for ETL pipeline
├── scripts/
│   └── setup.sh                # Local development setup script
.github/
└── workflows/
    ├── deploy.yml              # Blue-green deployment workflow
    └── deploy-ecs.yml          # Automated ECS deployment workflow
```

### File Descriptions

#### devops/Dockerfile.pipeline

This Dockerfile is used to build the Docker image for the data engineering ETL pipeline. It uses Python 3.11 as the base image and includes all necessary dependencies for running the pipeline.

Key features:

- Uses non-root user for security
- Installs libpq-dev and gcc for database connectivity
- Copies requirements from data-engineering directory
- Switches to pipeline user for execution

#### devops/scripts/setup.sh

A bash script that sets up the local development environment. It performs the following:

- Checks if Docker is installed
- Creates .env file with default values if not present
- Starts all services using docker-compose

#### .github/workflows/deploy.yml

This workflow implements a blue-green deployment strategy with manual triggers. It includes:

- Build and push images to ECR
- Deploy to blue environment (staging)
- Deploy to green environment (production)
- Automatic rollback on failure

#### .github/workflows/deploy-ecs.yml

This automated workflow triggers on push to main or developer branches. It:

- Builds all Docker images
- Pushes them to ECR
- Updates ECS services
- Handles CodeDeploy integration

---

## Infrastructure Components

### 1. Amazon ECR (Elastic Container Registry)

Amazon ECR provides a fully managed Docker container registry that makes it easy to store, manage, and deploy container images. The DataPulse project uses multiple ECR repositories for different components.

#### Repository List

| Repository Name      | Purpose                       | Image Scanning |
| -------------------- | ----------------------------- | -------------- |
| datapulse/backend    | FastAPI backend application   | Enabled        |
| datapulse/frontend   | Static frontend application   | Enabled        |
| datapulse/prometheus | Prometheus metrics collection | Enabled        |
| datapulse/grafana    | Grafana dashboards            | Enabled        |
| datapulse/loki       | Log aggregation               | Enabled        |

Each repository is configured with:

- Image scanning enabled on push to detect vulnerabilities
- Tag mutability set to MUTABLE to allow overwriting tags
- Lifecycle policies for automatic image cleanup

#### ECR Repository Terraform Configuration

The repositories are created using Terraform with the following configuration:

```hcl
resource "aws_ecr_repository" "backend" {
  name = "datapulse/backend"

  image_scanning_configuration {
    scan_on_push = true
  }

  image_tag_mutability = "MUTABLE"

  tags = {
    Description = "DataPulse Backend API"
    Environment = var.environment
  }
}
```

#### ECR Cross-Account Access

A repository policy is attached to allow ECS tasks to pull images:

```hcl
resource "aws_ecr_repository_policy" "backend" {
  repository = aws_ecr_repository.backend.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowCrossAccountPull"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Action = [
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability"
      ]
    }]
  })
}
```

### 2. ECS Cluster (Elastic Container Service)

Amazon ECS with Fargate provides serverless compute for containers. The cluster is configured with multiple capacity providers for cost optimization.

#### Cluster Configuration

- Cluster Name: datapulse-{environment}
- Capacity Providers: FARGATE (primary), FARGATE_SPOT (cost optimization)
- Container Insights: Enabled for enhanced monitoring
- VPC: Custom VPC with public and private subnets

#### ECS Task Execution Role

A dedicated IAM role is created for ECS task execution with the following permissions:

```hcl
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "datapulse-ecs-task-execution-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
```

#### ECS Task Role

A separate task role is created for application-specific AWS permissions:

```hcl
resource "aws_iam_role" "ecs_task_role" {
  name = "datapulse-ecs-task-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}
```

### 3. VPC Networking

A complete VPC infrastructure is provisioned to support the ECS clusters with proper network isolation and security.

#### VPC Configuration

- VPC CIDR Block: Configurable (default 10.0.0.0/16)
- DNS Hostnames: Enabled
- DNS Support: Enabled

#### Subnet Architecture

The networking uses a multi-subnet architecture across two availability zones:

- Public Subnet 1: 10.0.1.0/24 (availability zone a)
- Public Subnet 2: 10.0.2.0/24 (availability zone b)
- Private Subnet 1: 10.0.10.0/24 (availability zone a)
- Private Subnet 2: 10.0.20.0/24 (availability zone b)

Public subnets are used for:

- NAT Gateway
- Application Load Balancer nodes
- Internet Gateway attachment

Private subnets are used for:

- ECS tasks (no direct internet access)
- RDS database instances
- ElastiCache clusters

#### Internet Gateway

```hcl
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "datapulse-igw-${var.environment}"
    Environment = var.environment
  }
}
```

#### NAT Gateway

A NAT Gateway is deployed in the first public subnet to allow outbound internet access from private subnets:

```hcl
resource "aws_nat_gateway" "main_1" {
  allocation_id = aws_eip.nat_1.id
  subnet_id     = aws_subnet.public_1.id

  depends_on = [aws_internet_gateway.main]
}
```

#### Security Groups

Two security groups are created:

1. ALB Security Group: Allows inbound HTTP (80) and HTTPS (443) from anywhere
2. ECS Tasks Security Group: Allows traffic from ALB on ports 8000 (backend), 80 (frontend), and 3000 (Grafana)

```hcl
resource "aws_security_group" "ecs_tasks" {
  name        = "datapulse-ecs-tasks-${var.environment}"
  description = "Security group for ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "FastAPI HTTP from ALB"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

### 4. Application Load Balancer (ALB)

The Application Load Balancer distributes traffic across ECS services with built-in health checks and SSL termination.

#### ALB Configuration

- Load Balancer Name: datapulse-alb-{environment}
- Type: Application Load Balancer (Layer 7)
- Scheme: Internet-facing
- Subnets: Public subnets 1 and 2
- Security Groups: ALB security group
- Deletion Protection: Enabled for production environment

#### Target Groups

Multiple target groups are created for different services:

| Target Group Name             | Port | Protocol | Health Check Path |
| ----------------------------- | ---- | -------- | ----------------- |
| datapulse-backend-blue-{env}  | 8000 | HTTP     | /health           |
| datapulse-backend-green-{env} | 8000 | HTTP     | /health           |
| datapulse-frontend-{env}      | 80   | HTTP     | /health           |
| datapulse-prometheus-{env}    | 9090 | HTTP     | /metrics          |
| datapulse-grafana-{env}       | 3000 | HTTP     | /api/health       |

Health check configuration:

- Healthy threshold: 2
- Unhealthy threshold: 2
- Timeout: 5 seconds
- Interval: 30 seconds

```hcl
resource "aws_lb_target_group" "backend_blue" {
  name        = "datapulse-backend-blue-${var.environment}"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }
}
```

### 5. GitHub OIDC Integration

GitHub OpenID Connect (OIDC) integration provides secure, credential-less authentication between GitHub Actions and AWS. This eliminates the need to store long-lived AWS credentials as GitHub secrets.

#### OIDC Provider Configuration

```hcl
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com"
  ]

  thumbprint_list = [
    "6938fd4d98bab03fa1d2a9b30c2eb2b5d8c0d2d1"
  ]
}
```

#### IAM Role for GitHub Actions

The role is configured with a trust policy that restricts access to specific repository conditions:

```hcl
resource "aws_iam_role" "github_actions_deploy" {
  name = "github-actions-deploy-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:AmaliTech-Training-Academy/DataPulse_Team8:*"
          }
        }
      }
    ]
  })
}
```

#### Role Permissions Policy

The deployment role has scoped permissions for:

- ECR: Get authorization token, image push/pull operations
- ECS: Register task definitions, update services, describe resources
- ALB: Describe and modify listeners, target groups
- CodeDeploy: Create and manage deployments
- IAM: Pass role for ECS task execution
- Secrets Manager: Get secret values
- SSM Parameter Store: Get parameters
- CloudWatch Logs: Create log groups and streams

### 6. Secrets Management

AWS Secrets Manager provides secure storage for sensitive data with automatic rotation capabilities.

#### Secrets Created

| Secret Name                 | Contents                                 | Auto-rotation |
| --------------------------- | ---------------------------------------- | ------------- |
| datapulse/{env}/credentials | PostgreSQL user, password, database name | No            |
| datapulse/{env}/redis       | Redis endpoint, port, auth token         | No            |
| datapulse/{env}/app-secret  | Application JWT secret key               | No            |

#### Random Password Generation

Passwords are automatically generated using Terraform random_password resources:

```hcl
resource "random_password" "postgres" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}|;:,.<>?"

  keepers = {
    environment = var.environment
  }
}

resource "aws_secretsmanager_secret" "db_credentials" {
  name = "datapulse/${var.environment}/credentials"

  recovery_window_in_days = 7

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id

  secret_string = jsonencode({
    postgres_user     = var.postgres_user
    postgres_password = var.postgres_password != null ? var.postgres_password : random_password.postgres.result
    postgres_db       = var.postgres_db
  })
}
```

### 7. Additional AWS Services

#### Amazon RDS (Relational Database Service)

- Engine: PostgreSQL
- Instance Class: db.t3.medium (configurable)
- Multi-AZ: No (single AZ for dev)
- Storage: 20GB gp3
- Backup Retention: 7 days

#### Amazon ElastiCache (Redis)

- Engine: Redis
- Node Type: cache.t3.micro (dev)
- Number of Nodes: 2 (1 primary, 1 replica)
- Automatic Failover: Enabled
- Encryption: At rest and in transit

---

## CI/CD Pipelines

### Pipeline 1: Blue-Green Deployment (deploy.yml)

This workflow implements a comprehensive blue-green deployment strategy that allows testing in a staging environment before production rollout.

#### Workflow Triggers

- Manual workflow dispatch with environment selection (dev, staging, production)

#### Workflow Stages

1. **Build and Push Stage**
   - Checks out repository code
   - Configures AWS credentials using OIDC
   - Logs into ECR
   - Sets up Docker Buildx
   - Extracts metadata for Docker tags
   - Builds and pushes backend image
   - Builds and pushes pipeline ETL image

2. **Deploy Blue Stage** (Staging)
   - Creates blue task definition
   - Registers task definition with ECS
   - Updates blue service with new task definition
   - Waits for service stability
   - Runs health checks

3. **Deploy Green Stage** (Production - only on main branch)
   - Creates green task definition
   - Registers task definition with ECS
   - Updates green service
   - Waits for service stability
   - Switches ALB listener to green target group

4. **Rollback Stage** (on failure)
   - Gets previous stable task definition
   - Updates service with previous task definition

#### Job Configuration

```yaml
jobs:
  build-and-push:
    runs-on: ubuntu-latest
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}

  deploy-blue:
    needs: build-and-push
    runs-on: ubuntu-latest

  deploy-green:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

  rollback:
    needs: [deploy-blue, deploy-green]
    runs-on: ubuntu-latest
    if: failure()
```

### Pipeline 2: Automated ECS Deployment (deploy-ecs.yml)

This workflow provides automated deployment on every push to main or developer branches.

#### Workflow Triggers

- Push to main branch
- Push to developer branch

#### Concurrency Settings

```yaml
concurrency:
  group: deploy-production
  cancel-in-progress: true
```

This ensures only one deployment runs at a time, with in-progress deployments cancelled when a new commit is pushed.

#### Workflow Steps

1. **Checkout**: Pulls the latest code from the repository

2. **Environment Detection**: Determines target environment based on branch

3. **AWS OIDC Authentication**: Configures AWS credentials using OIDC role assumption

4. **Login to ECR**: Authenticates Docker to ECR registry

5. **Build Images**: Builds and pushes all required images:
   - Backend API (tagged with SHA and latest)
   - Frontend static files
   - Prometheus
   - Grafana
   - Loki

6. **Update Task Definition**: Modifies environment-specific values in task definition JSON

7. **Render Task Definition**: Uses AWS ECS task definition renderer action

8. **Stop Active Deployments**: Checks for and stops any in-progress CodeDeploy deployments

9. **Deploy to ECS**: Updates the ECS service with new task definition using CodeDeploy

10. **Restart Auxiliary Services**: Forces new deployment for frontend and monitoring services

#### Sample Deployment Command

```bash
docker build -t $ECR_REGISTRY/datapulse/backend:$IMAGE_TAG -t $ECR_REGISTRY/datapulse/backend:latest ./backend
docker push $ECR_REGISTRY/datapulse/backend:$IMAGE_TAG
docker push $ECR_REGISTRY/datapulse/backend:latest
```

---

## Challenges and Solutions

### Challenge 1: Docker Build Provenance Issues

#### Problem Description

When building Docker images with BuildKit enabled, the system encountered "broken pipe" errors during multi-architecture manifest creation. This was particularly problematic when pushing images to ECR as provenance attestation failed intermittently.

#### Root Cause

BuildKit's default behavior attempts to create provenance attestations and SBOM (Software Bill of Materials) manifests, which can cause network issues during the image push process.

#### Solution Implemented

Disabled provenance attestation and SBOM generation in Docker build commands:

```bash
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain
export DOCKER_DEFAULT_PLATFORM=linux/arm64

docker build \
  --provenance=false \
  --sbom=false \
  -t imagename:tag \
  -f Dockerfile \
  .
```

#### Why This Works

The --provenance=false flag prevents BuildKit from creating attestation manifests, while --sbom=false disables Software Bill of Materials generation. This significantly reduces the complexity of the build process and eliminates the broken pipe errors.

### Challenge 2: ECR Image Push Failures

#### Problem Description

Network timeouts and intermittent failures occurred when pushing large Docker images to ECR, particularly during peak hours or when using slow network connections.

#### Root Cause

- Network instability between build environment and AWS
- Large image sizes causing longer upload times
- Default Docker retry behavior not suitable for large images
- ECR connection timeouts

#### Solution Implemented

Implemented a robust retry mechanism with exponential backoff in the deployment script:

```bash
push_with_retry() {
  local tag="$1"
  local max_retries=5
  local attempt=1

  while [ $attempt -le $max_retries ]; do
    info "Push attempt ${attempt}/${max_retries}: ${tag}"
    if docker push "${tag}"; then
      return 0
    fi
    attempt=$((attempt + 1))
    warn "Push failed, retrying in 10s..."
    sleep 10
  done
  fail "Push failed after ${max_retries} attempts: ${tag}"
}
```

#### Additional Measures

- Reduced Docker image size by using multi-stage builds
- Used slim base images (python:3.11-slim)
- Implemented proper .dockerignore files
- Enabled layer caching where possible

### Challenge 3: GitHub Actions OIDC Authentication

#### Problem Description

The original implementation used long-lived AWS access keys stored as GitHub secrets, which presented security risks:

- Keys could be leaked through repository compromise
- Manual rotation required
- No way to restrict access to specific branches or PRs
- Keys could remain valid even after employee departure

#### Root Cause

Traditional IAM user-based authentication requires storing credentials in GitHub secrets, which is not a secure practice for production deployments.

#### Solution Implemented

Implemented OpenID Connect (OIDC) authentication:

1. **Created IAM OIDC Provider** in Terraform:

```hcl
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03fa1d2a9b30c2eb2b5d8c0d2d1"]
}
```

2. **Configured Trust Policy** with repository conditions:

```hcl
"Condition": {
  "StringLike": {
    "token.actions.githubusercontent.com:sub": "repo:AmaliTech-Training-Academy/DataPulse_Team8:*"
  }
}
```

3. **Created IAM Role** with scoped permissions:

```hcl
resource "aws_iam_role" "github_actions_deploy" {
  name = "github-actions-deploy-${var.environment}"
  # Trust policy configured above
}
```

4. **Updated GitHub Workflow** to use OIDC:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ env.GITHUB_OIDC_ROLE }}
    role-session-name: GitHubActions-${{ github.run_id }}
    aws-region: ${{ env.AWS_REGION }}
```

#### Benefits

- No long-lived credentials stored in GitHub
- Automatic token expiration
- Fine-grained access control based on repository and branch
- Audit trail through CloudTrail
- Easier compliance with security policies

### Challenge 4: Managing Secrets in ECS Tasks

#### Problem Description

Securely passing database credentials and API keys to ECS containers without:

- Hardcoding in Docker images
- Storing in environment variables that could be exposed
- Using insecure methods

#### Root Cause

ECS task definitions can expose environment variables in CloudWatch logs and task descriptions. Standard environment variables are not secure for sensitive data.

#### Solution Implemented

Used AWS Secrets Manager with ECS task definitions:

1. **Created Secrets** in Secrets Manager with Terraform

2. **Referenced Secrets in Task Definition**:

```json
{
  "family": "datapulse-task",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "account.dkr.ecr.region.amazonaws.com/datapulse/backend:latest",
      "essential": true,
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:datapulse/prod/credentials:DATABASE_URL::"
        },
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:datapulse/prod/app-secret:SECRET_KEY::"
        }
      ],
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ]
    }
  ]
}
```

3. **Granted ECS Task Role Permission** to read secrets:

```hcl
{
  "Effect": "Allow",
  "Action": [
    "secretsmanager:GetSecretValue",
    "secretsmanager:DescribeSecret"
  ],
  "Resource": "arn:aws:secretsmanager:region:account:secret:datapulse/*"
}
```

#### Security Benefits

- Secrets are encrypted at rest using AWS KMS
- No sensitive data in Docker images
- Secrets injected at container startup only
- IAM-based access control
- Audit logging through CloudTrail

### Challenge 5: Blue-Green Deployment with ALB

#### Problem Description

Achieving zero-downtime deployments by seamlessly switching traffic between blue (current) and green (new) environments:

- Need to test new version before production traffic
- Must be able to rollback quickly if issues arise
- ALB listener management required

#### Root Cause

Traditional deployments cause downtime during code updates. Blue-green deployment requires proper ALB configuration and traffic switching mechanisms.

#### Solution Implemented

1. **Created Two Target Groups** (blue and green):

```hcl
resource "aws_lb_target_group" "backend_blue" {
  name = "datapulse-backend-blue-${var.environment}"
  # ... configuration
}

resource "aws_lb_target_group" "backend_green" {
  name = "datapulse-backend-green-${var.environment}"
  # ... configuration
}
```

2. **Deployed to Inactive Target Group**:

```bash
aws ecs update-service \
  --cluster datapulse-prod \
  --service datapulse-backend-green-prod \
  --task-definition new-task-definition-arn \
  --force-new-deployment
```

3. **Waited for Health Checks**:

```bash
aws ecs wait services-stable \
  --cluster datapulse-prod \
  --services datapulse-backend-green-prod
```

4. **Switched ALB Listener**:

```bash
aws elbv2 modify-listener \
  --listener-arn ${{ secrets.ALB_LISTENER_ARN }} \
  --default-actions Type=forward,TargetGroupArn=${{ secrets.GREEN_TARGET_GROUP_ARN }}
```

#### Rollback Procedure

If health checks fail:

```bash
aws elbv2 modify-listener \
  --listener-arn ${{ secrets.ALB_LISTENER_ARN }} \
  --default-actions Type=forward,TargetGroupArn=${{ secrets.BLUE_TARGET_GROUP_ARN }}
```

### Challenge 6: Cross-Platform Docker Builds

#### Problem Description

Building Docker images on one platform architecture (AMD64) but deploying to another (ARM64), or vice versa, causing image compatibility issues.

#### Root Cause

Docker images built on AMD64 machines cannot run on ARM64 infrastructure without explicit platform specification or emulation.

#### Solution Implemented

Set explicit platform targets in build commands:

```bash
# For ARM64 build on AMD64 runner
export DOCKER_DEFAULT_PLATFORM=linux/arm64
docker build -t image:tag .

# For AMD64 build explicitly
docker build --platform linux/amd64 -t image:tag .
```

In GitHub Actions, this is handled in the workflow:

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build and push Backend API
  uses: docker/build-push-action@v5
  with:
    context: ./backend
    push: true
    tags: ${{ env.ECR_REGISTRY }}/datapulse/backend:${{ github.sha }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### Challenge 7: ECS Service Stability

#### Problem Description

Deployment scripts continued execution before ECS services were fully stable, causing race conditions and failed deployments.

#### Root Cause

ECS update-service returns immediately but the service may take several minutes to stabilize. Continuing without waiting causes failures when subsequent operations depend on service health.

#### Solution Implemented

Used the AWS ECS wait command to ensure service stability:

```bash
aws ecs wait services-stable \
  --region eu-west-1 \
  --cluster datapulse-prod \
  --services datapulse-backend-blue-prod
```

This command polls the ECS API until:

- All tasks reach RUNNING state
- Minimum healthy percent requirements are met
- Maximum unhealthy percent thresholds are not exceeded
- Or timeout is reached (default 40 minutes)

#### Implementation in Deploy Script

```bash
info "Waiting for ECS service to stabilize (this may take 2-5 minutes)..."
aws ecs wait services-stable \
  --region "${REGION}" \
  --cluster "${CLUSTER}" \
  --services "datapulse-backend-blue-dev"

if [ $? -eq 0 ]; then
  log "ECS service is stable and running!"
else
  warn "Service did not stabilize within timeout"
fi
```

### Challenge 8: CloudWatch Log Group Creation

#### Problem Description

ECS tasks failed to start with errors indicating CloudWatch log group did not exist, even though the awslogs driver was configured in task definitions.

#### Root Cause

ECS does not automatically create CloudWatch log groups. If the specified log group doesn't exist when a task starts, the task fails.

#### Solution Implemented

Created log groups before deployment as part of the deployment script:

```bash
# Ensure CloudWatch log group exists
aws logs create-log-group \
  --log-group-name "/ecs/datapulse-backend" \
  --region eu-west-1 2>/dev/null || true

# Set retention policy
aws logs put-retention-policy \
  --log-group-name "/ecs/datapulse-backend" \
  --retention-in-days 7 \
  --region eu-west-1 2>/dev/null || true
```

#### Terraform Alternative

Can also be created in Terraform:

```hcl
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/datapulse-${var.environment}"
  retention_in_days = 7

  tags = {
    Environment = var.environment
  }
}
```

---

## Commands Reference

### Docker Commands

#### Building Images

```bash
# Build backend image
docker build -t datapulse/backend:latest ./backend

# Build frontend image
docker build -t datapulse/frontend:latest ./frontend

# Build pipeline image
docker build -t datapulse/pipeline:latest -f devops/Dockerfile.pipeline .

# Build with no cache
docker build --no-cache -t datapulse/backend:latest ./backend

# Build with specific platform
docker build --platform linux/amd64 -t datapulse/backend:latest ./backend

# Build multiple tags
docker build -t datapulse/backend:latest -t datapulse/backend:v1.0.0 ./backend
```

#### Pushing and Pulling Images

```bash
# Login to ECR
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 384747604241.dkr.ecr.eu-west-1.amazonaws.com

# Push image to ECR
docker push 384747604241.dkr.ecr.eu-west-1.amazonaws.com/datapulse/backend:latest

# Push multiple tags
docker push 384747604241.dkr.ecr.eu-west-1.amazonaws.com/datapulse/backend:latest
docker push 384747604241.dkr.ecr.eu-west-.amazonaws.com/datapulse/backend:v1.0.0

# Pull image from ECR
docker pull 384747604241.dkr.ecr.eu-west-1.amazonaws.com/datapulse/backend:latest

# Pull official images
docker pull prom/prometheus:latest
docker pull prom/prometheus:v2.49.1
docker pull grafana/grafana:latest
docker pull grafana/grafana:10.3.3
docker pull grafana/loki:2.9.2

# Tag existing image
docker tag local-image:latest 384747604241.dkr.ecr.eu-west-1.amazonaws.com/datapulse/backend:latest
```

#### Managing Images

```bash
# List local images
docker images

# List images in ECR
aws ecr list-images --repository-name datapulse/backend --region eu-west-1

# Delete local image
docker rmi datapulse/backend:latest

# Delete image from ECR
aws ecr batch-delete-image \
  --repository-name datapulse/backend \
  --image-ids imageTag=latest \
  --region eu-west-1
```

### AWS ECS Commands

#### Cluster Management

```bash
# Create ECS cluster
aws ecs create-cluster \
  --cluster-name datapulse-dev \
  --region eu-west-1 \
  --capacity-providers FARGATE FARGATE_SPOT \
  --settings name=containerInsights,value=enabled

# List clusters
aws ecs list-clusters --region eu-west-1

# Describe cluster
aws ecs describe-cluster --cluster-name datapulse-prod --region eu-west-1

# Delete cluster
aws ecs delete-cluster --cluster-name datapulse-dev --region eu-west-1
```

#### Task Definitions

```bash
# Register task definition
aws ecs register-task-definition \
  --region eu-west-1 \
  --family datapulse-backend \
  --network-mode awsvpc \
  --requires-compatibilities FARGATE \
  --cpu 512 \
  --memory 1024 \
  --execution-role-arn arn:aws:iam::384747604241:role/datapulse-ecs-task-execution-dev \
  --task-role-arn arn:aws:iam::384747604241:role/datapulse-ecs-task-dev \
  --container-definitions file://task-definition.json

# List task definitions
aws ecs list-task-definitions --family-prefix datapulse-backend --region eu-west-1

# Describe task definition
aws ecs describe-task-definition --task-definition datapulse-backend:10 --region eu-west-1

# Deregister task definition
aws ecs deregister-task-definition --task-definition datapulse-backend:10 --region eu-west-1
```

#### Services

```bash
# Create service
aws ecs create-service \
  --cluster datapulse-prod \
  --service-name datapulse-backend-blue-prod \
  --task-definition datapulse-backend:10 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration file://network-config.json \
  --loadBalancers file://loadbalancers.json \
  --region eu-west-1

# Update service
aws ecs update-service \
  --region eu-west-1 \
  --cluster datapulse-prod \
  --service datapulse-backend-blue-prod \
  --task-definition <task-definition-arn> \
  --desired-count 1 \
  --force-new-deployment

# Describe service
aws ecs describe-services \
  --cluster datapulse-prod \
  --services datapulse-backend-blue-prod \
  --region eu-west-1

# List services
aws ecs list-services --cluster datapulse-prod --region eu-west-1
```

#### Task Management

```bash
# List running tasks
aws ecs list-tasks \
  --cluster datapulse-prod \
  --service-name datapulse-backend-blue-prod \
  --region eu-west-1

# Describe task
aws ecs describe-tasks \
  --cluster datapulse-prod \
  --tasks <task-arn> \
  --region eu-west-1

# Run task (one-off)
aws ecs run-task \
  --cluster datapulse-prod \
  --task-definition datapulse-backend \
  --count 1 \
  --launch-type FARGATE \
  --region eu-west-1

# Stop task
aws ecs stop-task \
  --cluster datapulse-prod \
  --task <task-arn> \
  --region eu-west-1
```

#### Waiting for Stability

```bash
# Wait for service to be stable
aws ecs wait services-stable \
  --region eu-west-1 \
  --cluster datapulse-prod \
  --services datapulse-backend-blue-prod

# Wait for tasks to stop
aws ecs wait tasks-stopped \
  --region eu-west-1 \
  --cluster datapulse-prod \
  --tasks <task-arn>
```

### AWS ECR Commands

```bash
# Create repository
aws ecr create-repository \
  --repository-name datapulse/backend \
  --image-scanning-configuration scanOnPush=true \
  --image-tag-mutability MUTABLE \
  --region eu-west-1

# List repositories
aws ecr describe-repositories --region eu-west-1

# Describe repository
aws ecr describe-repositories --repository-names datapulse/backend --region eu-west-1

# Delete repository
aws ecr delete-repository \
  --repository-name datapulse/backend \
  --force \
  --region eu-west-1

# Get authorization token
aws ecr get-authorization-token --region eu-west-1
```

### AWS ALB Commands

```bash
# Describe load balancers
aws elbv2 describe-load-balancers --region eu-west-1

# Describe target groups
aws elbv2 describe-target-groups --region eu-west-1

# Describe target group attributes
aws elbv2 describe-target-group-attributes \
  --target-group-arn <target-group-arn> \
  --region eu-west-1

# Describe target health
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn> \
  --region eu-west-1

# Modify listener
aws elbv2 modify-listener \
  --listener-arn <listener-arn> \
  --default-actions Type=forward,TargetGroupArn=<target-group-arn> \
  --region eu-west-1

# Register targets
aws elbv2 register-targets \
  --target-group-arn <target-group-arn> \
  --targets Id=10.0.1.10,Port=8000 \
  --region eu-west-1

# Deregister targets
aws elbv2 deregister-targets \
  --target-group-arn <target-group-arn> \
  --targets Id=10.0.1.10 \
  --region eu-west-1
```

### Terraform Commands

```bash
# Initialize Terraform
cd terraform
terraform init

# Format configuration files
terraform fmt

# Validate configuration
terraform validate

# Plan infrastructure changes
terraform plan -var-file=prod.tfvars

# Apply infrastructure changes
terraform apply -var-file=prod.tfvars

# Apply with auto-approve
terraform apply -var-file=prod.tfvars -auto-approve

# Destroy infrastructure
terraform destroy -var-file=prod.tfvars

# Destroy with auto-approve
terraform destroy -var-file=prod.tfvars -auto-approve

# Get outputs
terraform output

# Show current state
terraform show

# List resources in state
terraform state list

# Show specific resource
terraform state show aws_ecs_cluster.main

# Import existing resource
terraform import aws_ecs_cluster.main datapulse-prod

# Refresh state
terraform refresh
```

### GitHub Actions Commands

Using `act` for local workflow testing:

```bash
# Install act (macOS)
brew install act

# Run workflow locally
act -W .github/workflows/deploy-ecs.yml

# Run specific job
act -j build-and-push

# Run with specific event
act -W .github/workflows/deploy.yml -e event.json

# Run with secrets
act -s AWS_ACCESS_KEY_ID=xxx -s AWS_SECRET_ACCESS_KEY=xxx

# List workflows
act -l
```

### Deployment Script Commands

```bash
# Make deployment script executable
chmod +x deploy-to-ecr.sh

# Run deployment with specific tag
./deploy-to-ecr.sh v1.0.0

# Run deployment with latest tag
./deploy-to-ecr.sh latest

# Run deployment with custom SHA
./deploy-to-ecr.sh abc123def
```

### Local Development Commands

```bash
# Start all services
docker-compose up -d

# Start with build
docker-compose up --build -d

# Start with profile
docker-compose --profile de up -d

# View logs
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs --tail=100 backend

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild specific service
docker-compose build backend
docker-compose up -d --no-deps backend

# Scale service
docker-compose up -d --scale backend=2

# Run one-off command
docker-compose exec backend python manage.py migrate
```

---

## Environment Variables

### AWS Configuration

| Variable              | Description              | Required | Example      |
| --------------------- | ------------------------ | -------- | ------------ |
| AWS_REGION            | AWS region for resources | Yes      | eu-west-1    |
| AWS_ACCOUNT_ID        | AWS account ID           | Yes      | 384747604241 |
| AWS_ACCESS_KEY_ID     | AWS access key           | No\*     | -            |
| AWS_SECRET_ACCESS_KEY | AWS secret key           | No\*     | -            |
| AWS_SESSION_TOKEN     | AWS session token        | No       | -            |

\*Required for local development; CI/CD uses OIDC authentication

### GitHub Secrets

Configure these in GitHub repository settings under Secrets and variables:

| Secret Name            | Description                          | Required |
| ---------------------- | ------------------------------------ | -------- |
| GITHUB_OIDC_ROLE_ARN   | IAM role ARN for OIDC authentication | Yes      |
| ECR_REGISTRY           | ECR registry URL                     | Yes      |
| ECS_CLUSTER            | ECS cluster name                     | Yes      |
| ECS_EXECUTION_ROLE     | ECS task execution role ARN          | Yes      |
| ECS_SECRET_ARN         | Secrets Manager secret ARN           | Yes      |
| ALB_LISTENER_ARN       | ALB listener ARN                     | Yes      |
| GREEN_TARGET_GROUP_ARN | Green target group ARN               | Yes      |
| AWS_ACCOUNT_ID         | AWS account ID                       | No       |

### Application Variables

| Variable          | Description                  | Default                             |
| ----------------- | ---------------------------- | ----------------------------------- |
| DATABASE_URL      | PostgreSQL connection string | postgresql://user:pass@host:5432/db |
| SECRET_KEY        | Application secret key       | Auto-generated                      |
| ENVIRONMENT       | Environment name             | development                         |
| POSTGRES_USER     | Database username            | datapulse                           |
| POSTGRES_PASSWORD | Database password            | -                                   |
| POSTGRES_DB       | Database name                | datapulse                           |
| POSTGRES_HOST     | Database host                | localhost                           |
| POSTGRES_PORT     | Database port                | 5432                                |

### Monitoring Variables

| Variable               | Description            | Default |
| ---------------------- | ---------------------- | ------- |
| GRAFANA_ADMIN_USER     | Grafana admin username | admin   |
| GRAFANA_ADMIN_PASSWORD | Grafana admin password | -       |
| PROMETHEUS_PORT        | Prometheus port        | 9090    |
| GRAFANA_PORT           | Grafana port           | 3000    |
| LOKI_PORT              | Loki port              | 3100    |

---

## Deployment Workflows

### Manual Deployment using deploy-to-ecr.sh

This script provides a comprehensive deployment process for manual execution:

1. Verifies AWS credentials
2. Logs into ECR
3. Ensures CloudWatch log group exists
4. Builds backend and frontend images
5. Pulls and tags monitoring images
6. Pushes all images to ECR with retry logic
7. Registers new ECS task definition
8. Updates ECS service
9. Waits for service stability
10. Verifies ALB health

```bash
# Full deployment
./deploy-to-ecr.sh v1.0.0

# Check ALB health
curl http://datapulse-alb-dev-810866140.eu-west-1.elb.amazonaws.com/health
```

### Automated GitHub Actions Deployment

1. Developer pushes code to main branch
2. GitHub Actions workflow triggers automatically
3. Code is built and tested
4. Docker images are built and pushed to ECR
5. ECS task definition is updated
6. ECS service is updated with new task definition
7. CodeDeploy handles blue-green traffic switch
8. Monitoring services are restarted

### Rollback Procedure

If deployment fails:

1. **Automatic Rollback**: GitHub Actions has automatic rollback on failure
2. **Manual Rollback**: Switch ALB back to previous target group
3. **Task Definition Rollback**: Use previous task definition

```bash
# Manual rollback - switch ALB back
aws elbv2 modify-listener \
  --listener-arn <listener-arn> \
  --default-actions Type=forward,TargetGroupArn=<blue-target-group-arn>
```

---

## Local Development Setup

### Prerequisites

- Docker Desktop or Docker Engine
- Docker Compose
- AWS CLI (for ECR login)
- Git

### Setup Steps

1. Clone the repository:

```bash
git clone https://github.com/AmaliTech-Training-Academy/DataPulse_Team8.git
cd DataPulse_Team8
```

2. Run the setup script:

```bash
./devops/scripts/setup.sh
```

The script will:

- Check if Docker is installed
- Create .env file with default values if not present
- Start all services using docker-compose

3. Verify services are running:

```bash
docker-compose ps
```

4. Access services:

- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

### Manual Docker Compose Usage

1. Create .env file:

```bash
cp .env.example .env
# Edit .env with your values
```

2. Start services:

```bash
docker-compose up -d
```

3. View logs:

```bash
docker-compose logs -f
```

4. Stop services:

```bash
docker-compose down
```

---

## Troubleshooting

### ECS Task Not Starting

**Symptoms**: Tasks stay in PENDING state or fail to start

**Possible Causes**:

- Security group not allowing traffic
- Task definition has errors
- Image pull failure
- Insufficient resources (CPU/memory)

**Debugging Steps**:

1. Check task status:

```bash
aws ecs describe-tasks \
  --cluster datapulse-prod \
  --tasks <task-id> \
  --region eu-west-1
```

2. Check service events:

```bash
aws ecs describe-services \
  --cluster datapulse-prod \
  --services <service-name> \
  --region eu-west-1
```

3. Check CloudWatch logs:

```bash
aws logs get-log-events \
  --log-group-name /ecs/datapulse-backend \
  --log-stream-name ecs/backend/<task-id> \
  --region eu-west-1
```

**Solutions**:

- Verify security group allows traffic from ALB
- Check task definition JSON for syntax errors
- Verify ECR image exists and is accessible
- Check if CPU/memory limits are sufficient

### ALB Health Check Failures

**Symptoms**: Targets show unhealthy in ALB target group

**Possible Causes**:

- Container port mismatch
- Health check path incorrect
- Application not responding
- Security group blocking traffic

**Debugging Steps**:

1. Check target health:

```bash
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn> \
  --region eu-west-1
```

2. Test health endpoint directly:

```bash
curl http://<container-ip>:8000/health
```

3. Check security group rules

**Solutions**:

- Verify container port matches target group port
- Ensure health check path returns 200 status
- Verify application is running in container
- Check ALB security group allows outbound to ECS tasks

### Image Push Fails

**Symptoms**: Docker push to ECR fails with authentication or network errors

**Possible Causes**:

- ECR login token expired
- Network connectivity issues
- Docker build errors
- Insufficient ECR permissions

**Debugging Steps**:

1. Re-authenticate to ECR:

```bash
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin <registry>
```

2. Check if image exists locally:

```bash
docker images
```

3. Verify ECR permissions:

```bash
aws ecr describe-repositories
```

**Solutions**:

- Refresh ECR login before each push
- Check network connectivity to AWS
- Fix Docker build errors
- Verify IAM role has ECR permissions

### GitHub Actions OIDC Failure

**Symptoms**: GitHub workflow fails with "Access Denied" or "Security Token" errors

**Possible Causes**:

- OIDC role not properly configured
- Repository condition mismatch in trust policy
- Thumbprint not updated
- Role permissions incorrect

**Debugging Steps**:

1. Verify OIDC provider exists:

```bash
aws iam get-open-id-connect-provider \
  --open-id-connect-provider-arn <provider-arn>
```

2. Verify role exists:

```bash
aws iam get-role --role-name github-actions-deploy-prod
```

3. Check CloudTrail for denied actions

**Solutions**:

- Update trust policy with correct repository name
- Update thumbprint list for OIDC provider
- Verify role has required permissions
- Check GitHub OIDC provider configuration

### Terraform State Issues

**Symptoms**: Terraform apply fails with state errors or resource drift

**Possible Causes**:

- State file corruption
- Concurrent state modifications
- Backend configuration issues
- Manual resource changes

**Debugging Steps**:

1. Refresh state:

```bash
terraform refresh
```

2. Show current state:

```bash
terraform show
```

3. List resources:

```bash
terraform state list
```

**Solutions**:

- Use remote backend for state storage
- Implement state locking
- Use terraform import for existing resources
- Review and fix state manually if needed

---

## Best Practices

### Security

1. Always use OIDC instead of stored credentials
2. Implement least-privilege IAM policies
3. Use Secrets Manager for all sensitive data
4. Enable encryption at rest for all AWS resources
5. Regular security scanning of container images
6. Use private subnets for sensitive workloads
7. Enable VPC flow logs for network monitoring

### Deployment

1. Use blue-green deployment for production
2. Always wait for service stability after updates
3. Implement proper health checks
4. Use rolling updates with appropriate parameters
5. Test deployments in staging first
6. Maintain rollback capability
7. Monitor deployment metrics

### Infrastructure as Code

1. Use Terraform for all AWS resources
2. Implement proper state management with remote backend
3. Use variables for environment-specific configuration
4. Version control all infrastructure code
5. Implement proper testing (terratest, checkov)
6. Use modules for reusable components

### Monitoring and Logging

1. Enable Container Insights for ECS
2. Configure proper CloudWatch log retention
3. Set up alerts for critical metrics
4. Use structured logging in applications
5. Implement distributed tracing
6. Regular review of monitoring dashboards

### CI/CD

1. Implement proper branching strategy
2. Use environment-specific workflows
3. Implement proper secret management
4. Add automated testing in pipeline
5. Use caching to speed up builds
6. Implement proper approval gates for production

---

## Version History

| Version | Date | Changes                      |
| ------- | ---- | ---------------------------- |
| 1.0.0   | 2024 | Initial DevOps documentation |

---

This documentation provides a comprehensive guide to the DataPulse DevOps infrastructure, including detailed explanations of all components, challenges faced during implementation, and extensive command references for daily operations.
