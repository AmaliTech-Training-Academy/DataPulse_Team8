# =====================================================
# EC2 Instance for Development Environment
# =====================================================

# EC2 Security Group
resource "aws_security_group" "ec2_dev" {
  name        = "datapulse-ec2-dev-${var.environment}"
  description = "Security group for DataPulse Development EC2"
  vpc_id      = aws_vpc.main.id

  # SSH from anywhere (restrict in production)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH"
  }

  # HTTP from anywhere
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP"
  }

  # HTTPS from anywhere
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS"
  }

  # Application port (8000)
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "FastAPI"
  }

  # Grafana (3000)
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Grafana"
  }

  # Prometheus (9090)
  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Prometheus"
  }

  # Allow all outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "datapulse-ec2-dev-sg-${var.environment}"
    Environment = var.environment
  }
}

# IAM Role for EC2
resource "aws_iam_role" "ec2_dev" {
  name = "datapulse-ec2-dev-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = {
    Environment = var.environment
  }
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "ec2_dev" {
  name = "datapulse-ec2-dev-profile-${var.environment}"
  role = aws_iam_role.ec2_dev.name

  tags = {
    Environment = var.environment
  }
}

# IAM Policy for EC2 to access ECR
resource "aws_iam_policy" "ec2_ecr" {
  name        = "datapulse-ec2-ecr-policy-${var.environment}"
  description = "Policy for EC2 to pull from ECR"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:GetRepositoryPolicy",
        "ecr:DescribeRepositories",
        "ecr:ListImages"
      ]
      Resource = "*"
    }]
  })

  tags = {
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "ec2_ecr" {
  role       = aws_iam_role.ec2_dev.name
  policy_arn = aws_iam_policy.ec2_ecr.arn
}

# EC2 Key Pair - Generate or use provided
resource "aws_key_pair" "ec2_dev" {
  key_name   = "datapulse-ec2-dev-${var.environment}"
  public_key = var.ec2_public_key != "" ? var.ec2_public_key : (var.generate_ssh_key ? tls_private_key.ec2_gen[0].public_key_openssh : "")

  tags = {
    Name        = "datapulse-ec2-key-${var.environment}"
    Environment = var.environment
  }
}

# Generate SSH key pair if not provided
resource "tls_private_key" "ec2_gen" {
  count     = var.ec2_public_key == "" && var.generate_ssh_key ? 1 : 0
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Store private key in Secrets Manager
resource "aws_secretsmanager_secret" "ec2_ssh_key" {
  count = var.ec2_public_key == "" && var.generate_ssh_key ? 1 : 0
  name  = "datapulse/${var.environment}/ec2-ssh-key"

  recovery_window_in_days = 7

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

resource "aws_secretsmanager_secret_version" "ec2_ssh_key" {
  count     = var.ec2_public_key == "" && var.generate_ssh_key ? 1 : 0
  secret_id = aws_secretsmanager_secret.ec2_ssh_key[0].id

  secret_string = jsonencode({
    private_key = tls_private_key.ec2_gen[0].private_key_pem
    public_key  = tls_private_key.ec2_gen[0].public_key_openssh
    key_name    = aws_key_pair.ec2_dev.key_name
  })
}

# EC2 Instance - Development
resource "aws_instance" "dev" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = "t3.medium"
  subnet_id     = aws_subnet.public_1.id

  # Security Group
  vpc_security_group_ids = [aws_security_group.ec2_dev.id]

  # Key Pair
  key_name = aws_key_pair.ec2_dev.key_name

  # IAM Instance Profile
  iam_instance_profile = aws_iam_instance_profile.ec2_dev.name

  # User Data - Bootstrap Script
  user_data = templatefile("${path.module}/scripts/userdata.tpl", {
    environment    = var.environment
    ecs_cluster    = aws_ecs_cluster.main.name
    region         = var.aws_region
    AWS_ACCOUNT_ID = data.aws_caller_identity.current.account_id
    github_repo    = "https://github.com/your-org/DataPulse.git"
    github_branch  = "develop"
  })

  # Root Volume
  root_block_device {
    volume_size = 30
    volume_type = "gp3"
    encrypted   = true
  }

  # Tags
  tags = {
    Name        = "datapulse-dev-${var.environment}"
    Environment = var.environment
    Project     = "DataPulse"
    Role        = "Development"
  }

  # Lifecycle
  lifecycle {
    create_before_destroy = true
  }
}

# Get latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# EC2 Outputs
output "ec2_public_ip" {
  description = "EC2 public IP address"
  value       = aws_instance.dev.public_ip
}

output "ec2_public_dns" {
  description = "EC2 public DNS"
  value       = aws_instance.dev.public_dns
}

output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.dev.id
}

output "ec2_private_ip" {
  description = "EC2 private IP address"
  value       = aws_instance.dev.private_ip
}
