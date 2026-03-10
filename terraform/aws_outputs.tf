# ============================================================
# AWS Outputs for ECS/ECR Deployment
# ============================================================

# ECR Repository
output "ecr_repository_url" {
  description = "ECR repository URL for backend"
  value       = aws_ecr_repository.backend.repository_url
}

# ECS Cluster
output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

# ECS Service
output "ecs_service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.backend.name
}

# Application Load Balancer
output "alb_dns_name" {
  description = "ALB DNS name (use this to access the application)"
  value       = aws_lb.main.dns_name
}

output "alb_arn" {
  description = "ALB ARN"
  value       = aws_lb.main.arn
}

# RDS Database
output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.main.endpoint
}

output "rds_arn" {
  description = "RDS PostgreSQL ARN"
  value       = aws_db_instance.main.arn
}

# VPC
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = [aws_subnet.public_1.id, aws_subnet.public_2.id]
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = [aws_subnet.private_1.id, aws_subnet.private_2.id]
}

# Database Connection String
output "database_url" {
  description = "PostgreSQL connection URL"
  value       = "postgresql://${var.postgres_user}:${var.postgres_password}@${aws_db_instance.main.endpoint}/${var.postgres_db}"
  sensitive   = true
}

# Application URLs
output "application_urls" {
  description = "Application URLs after deployment"
  value = {
    backend_api  = "http://${aws_lb.main.dns_name}"
    backend_docs = "http://${aws_lb.main.dns_name}/docs"
    health       = "http://${aws_lb.main.dns_name}/health"
  }
}

# Estimated Monthly Cost
output "estimated_monthly_cost" {
  description = "Estimated monthly AWS cost breakdown"
  value = {
    ecs_fargate    = "~$15-25 (Fargate compute)"
    rds_postgres   = "~$15-20 (db.t3.micro, 20GB)"
    nat_gateway    = "~$30 (NAT Gateway)"
    alb            = "~$15-20 (Application LB)"
    data_transfer  = "~$5-10"
    ecr_storage    = "~$1-5"
    cloudwatch     = "~$0-5"
    total_estimate = "~$80-105/month"
    budget_tip     = "Use db.t3.micro and 1 task to stay under $100"
  }
}

# Terraform State Bucket
output "terraform_state_bucket" {
  description = "S3 bucket for Terraform state"
  value       = aws_s3_bucket.terraform_state.id
}

# Commands to deploy
output "deployment_commands" {
  description = "Commands to deploy the application"
  value = {
    initial_setup = <<-EOT
      # 1. Initialize Terraform
      cd terraform
      terraform init

      # 2. Plan the deployment
      terraform plan -var-file=prod.tfvars

      # 3. Apply the deployment
      terraform apply -var-file=prod.tfvars

      # 4. Build and push Docker image to ECR
      aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${aws_ecr_repository.backend.repository_url}
      docker build -t ${aws_ecr_repository.backend.repository_url}:latest ./backend
      docker push ${aws_ecr_repository.backend.repository_url}:latest

      # 5. Update ECS service to use new image
      aws ecs update-service --cluster datapulse-cluster --service datapulse-backend-service --force-new-deployment
    EOT
  }
}
