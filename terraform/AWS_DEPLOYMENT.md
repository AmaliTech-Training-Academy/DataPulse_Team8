# AWS ECS/ECR Deployment Guide

## Required AWS Credentials

### GitHub Secrets

Configure these in your GitHub repository settings (`Settings` → `Secrets and variables` → `Actions`):

| Secret Name             | Description             | How to Get                                                                                                                   |
| ----------------------- | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `AWS_ACCESS_KEY_ID`     | AWS IAM User Access Key | 1. Go to AWS Console → IAM → Users → [Your User]<br>2. Security credentials → Create access key<br>3. Copy the Access key ID |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM User Secret     | Same as above - shown only once when creating the key                                                                        |

### IAM User Requirements

The AWS user whose credentials you use must have these permissions:

- `AmazonEC2FullAccess` or specific VPC/Subnet/ENI permissions
- `AmazonECS_FullAccess` or specific ECS permissions
- `AmazonECR_FullAccess` or specific ECR permissions
- `AmazonRDS_FullAccess` or specific RDS permissions
- `IAMFullAccess` or specific IAM role permissions
- `AmazonS3FullAccess` for Terraform state storage

### Recommended: Create a Dedicated IAM User

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*",
        "ecs:*",
        "ecr:*",
        "rds:*",
        "iam:*",
        "s3:*",
        "logs:*",
        "elasticloadbalancing:*"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Environment Variables Used

### GitHub Actions Workflow (aws-deploy.yml)

| Variable         | Value                       | Description         |
| ---------------- | --------------------------- | ------------------- |
| `AWS_REGION`     | `us-east-1`                 | AWS region          |
| `ECR_REPOSITORY` | `datapulse-backend`         | ECR repository name |
| `ECS_CLUSTER`    | `datapulse-cluster`         | ECS cluster name    |
| `ECS_SERVICE`    | `datapulse-backend-service` | ECS service name    |

---

## Terraform Variables (prod.tfvars)

| Variable                    | Example Value        | Description               |
| --------------------------- | -------------------- | ------------------------- |
| `aws_region`                | `us-east-1`          | AWS region                |
| `project_name`              | `datapulse`          | Resource naming prefix    |
| `environment`               | `production`         | Environment name          |
| `db_instance_class`         | `db.t3.micro`        | RDS instance type         |
| `db_allocated_storage`      | `20`                 | RDS storage in GB         |
| `postgres_user`             | `datapulse`          | Database username         |
| `postgres_password`         | `SecurePassword123!` | Database password         |
| `postgres_db`               | `datapulse`          | Database name             |
| `ecs_cpu_backend`           | `256`                | ECS CPU units (0.25 vCPU) |
| `ecs_memory_backend`        | `512`                | ECS memory in MB          |
| `ecs_service_desired_count` | `1`                  | Number of tasks           |

---

## Deployment Commands

### Manual Deployment (CLI)

```bash
# 1. Navigate to terraform directory
cd terraform

# 2. Initialize Terraform
terraform init

# 3. Plan deployment
terraform plan -var-file=prod.tfvars

# 4. Apply deployment
terraform apply -var-file=prod.tfvars

# 5. Get outputs
terraform output
```

### Build and Push Docker Image

```bash
# Get ECR login password
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ECR_URI

# Build image
docker build -t datapulse-backend:latest ./backend

# Tag for ECR
docker tag datapulse-backend:latest YOUR-ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com/datapulse-backend:latest

# Push to ECR
docker push YOUR-ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com/datapulse-backend:latest

# Trigger ECS deployment
aws ecs update-service \
  --cluster datapulse-cluster \
  --service datapulse-backend-service \
  --force-new-deployment
```

---

## Cost Breakdown (Monthly)

| Service         | Configuration            | Est. Cost   |
| --------------- | ------------------------ | ----------- |
| ECS Fargate     | 1 task, 0.25 vCPU, 512MB | $15-25      |
| RDS PostgreSQL  | db.t3.micro, 20GB        | $15-20      |
| NAT Gateway     | 1 NAT Gateway            | ~$30        |
| Application LB  | 1 ALB                    | $15-20      |
| Data Transfer   | ~10GB/month              | $5-10       |
| ECR Storage     | ~1GB                     | $1          |
| CloudWatch Logs | ~1GB                     | $0-3        |
| **Total**       |                          | **~$80-95** |

### Budget Tips to Stay Under $100

1. Use `db.t3.micro` (free tier eligible for new AWS accounts)
2. Keep ECS task count at 1
3. Use minimal CPU/memory (256 CPU, 512 MB)
4. Enable S3 lifecycle policies for Terraform state
5. Monitor usage with AWS Budgets alerts

---

## Troubleshooting

### Common Issues

#### 1. "Access Denied" when running Terraform

- Verify AWS credentials have correct IAM permissions
- Check that credentials are not expired

#### 2. ECS service fails to start

- Check CloudWatch logs: `aws logs get-log-events --log-group-name /ecs/datapulse-backend`
- Verify security groups allow traffic on port 8000
- Check that RDS is in same VPC as ECS tasks

#### 3. Image pull failure

- Verify ECR repository exists: `aws ecr describe-repositories`
- Check that ECS task has IAM permission to pull from ECR
- Verify image was pushed successfully

#### 4. High AWS costs

- Enable AWS Budgets alerts
- Use AWS Cost Explorer to monitor
- Consider using Spot instances for non-production
- Set up auto-scaling limits
