# =====================================================
# GitHub OIDC Provider and IAM Role for GitHub Actions
# This enables secure, credential-less AWS authentication
# for GitHub Actions workflows using OIDC
# =====================================================

# GitHub OIDC Provider
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com"
  ]

  thumbprint_list = [
    # GitHub's OIDC thumbprint (updated periodically)
    # This is the thumbprint for the GitHub OIDC provider
    # See: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect
    "6938fd4d98bab03fa1d2a9b30c2eb2b5d8c0d2d1"
  ]

  tags = {
    Description = "GitHub OIDC Provider for Actions"
    Environment = var.environment
  }
}

# IAM Role for GitHub Actions - Development
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
            # Allow from any repository in the organization
            # Format: repo:owner:ref
            # Adjust this to match your specific repository
            "token.actions.githubusercontent.com:sub" = "repo:AmaliTech-Training-Academy/DataPulse_Team8:*"
          }
        }
      }
    ]
  })

  description = "IAM role for GitHub Actions deployment to ${var.environment}"
  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# IAM Role Policy - Permissions for ECS Deployment
resource "aws_iam_role_policy" "github_actions_ecs_deploy" {
  name = "github-actions-ecs-deploy-${var.environment}"
  role = aws_iam_role.github_actions_deploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # ECR base permissions
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      },
      # ECR image push permissions (restricted to all datapulse repos to support backend, frontend, loki, etc)
      {
        Effect = "Allow"
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:PutImage"
        ]
        Resource = "arn:aws:ecr:${var.aws_region}:${data.aws_caller_identity.current.account_id}:repository/datapulse/*"
      },
      # ECS task definition permissions (requires wildcard resource)
      {
        Effect = "Allow"
        Action = [
          "ecs:RegisterTaskDefinition"
        ]
        Resource = "*"
      },
      # ECS service permissions
      {
        Effect = "Allow"
        Action = [
          "ecs:UpdateService",
          "ecs:DescribeServices",
          "ecs:ListTasks",
          "ecs:DescribeTasks"
        ]
        Resource = [
          "arn:aws:ecs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:service/datapulse-${var.environment}/*",
          "arn:aws:ecs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:cluster/datapulse-${var.environment}"
        ]
      },
      # Describe task definitions
      {
        Effect = "Allow"
        Action = [
          "ecs:DescribeTaskDefinition",
          "ecs:ListTaskDefinitions"
        ]
        Resource = "*"
      },
      # ALB permissions for blue-green deployment
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:DescribeListeners",
          "elasticloadbalancing:ModifyListener",
          "elasticloadbalancing:DescribeTargetGroups",
          "elasticloadbalancing:DescribeRules",
          "elasticloadbalancing:ModifyRule"
        ]
        Resource = "*"
      },
      # CodeDeploy permissions for blue-green deployment
      {
        Effect = "Allow"
        Action = [
          "codedeploy:CreateApplication",
          "codedeploy:GetApplication",
          "codedeploy:GetDeploymentGroup",
          "codedeploy:ListApplications",
          "codedeploy:ListDeploymentGroups",
          "codedeploy:CreateDeploymentGroup",
          "codedeploy:DeployApplication",
          "codedeploy:GetDeployment",
          "codedeploy:GetDeploymentConfig",
          "codedeploy:RegisterApplicationRevision",
          "codedeploy:ListDeployments",
          "codedeploy:StopDeployment"
        ]
        Resource = "*"
      },
      # IAM pass role for ECS task execution
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = [
          aws_iam_role.ecs_task_execution_role.arn,
          aws_iam_role.ecs_task_role.arn
        ]
      },
      # Secrets Manager for ECS secrets
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:datapulse/*"
      },
      # SSM Parameter Store
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:DescribeParameters"
        ]
        Resource = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/datapulse/*"
      },
      # CloudWatch Logs
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/ecs/datapulse-${var.environment}/*"
      }
    ]
  })
}

# IAM Role for GitHub Actions - Read Only (for CI/CD testing)
resource "aws_iam_role" "github_actions_readonly" {
  name = "github-actions-readonly-${var.environment}"

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

  description = "IAM role for GitHub Actions read-only access to ${var.environment}"
  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# Read-only policy
resource "aws_iam_role_policy" "github_actions_readonly" {
  name = "github-actions-readonly-${var.environment}"
  role = aws_iam_role.github_actions_readonly.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:DescribeImages",
          "ecr:DescribeRepositories"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:DescribeServices",
          "ecs:DescribeClusters",
          "ecs:ListServices",
          "ecs:ListClusters"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:DescribeLogGroups"
        ]
        Resource = "*"
      }
    ]
  })
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# Output the role ARN for GitHub Actions configuration
output "github_deploy_role_arn" {
  description = "ARN of the IAM role for GitHub Actions deployment"
  value       = aws_iam_role.github_actions_deploy.arn
}

output "github_readonly_role_arn" {
  description = "ARN of the IAM role for GitHub Actions read-only access"
  value       = aws_iam_role.github_actions_readonly.arn
}

output "github_oidc_provider_arn" {
  description = "ARN of the GitHub OIDC Provider"
  value       = aws_iam_openid_connect_provider.github.arn
}
