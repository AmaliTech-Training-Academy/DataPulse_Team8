#!/bin/bash
# EC2 Bootstrap Script for DataPulse Development Environment
# This script runs on first boot to set up Docker, Docker Compose, and the application

set -e

echo "=== DataPulse Development Environment Bootstrap ==="
echo "Environment: ${environment}"
echo "Region: ${region}"
echo "ECS Cluster: ${ecs_cluster}"
echo "GitHub Branch: ${github_branch}"

# Update system
echo "Updating system packages..."
yum update -y

# Install Docker
echo "Installing Docker..."
amazon-linux-extras install docker -y
systemctl start docker
systemctl enable docker

# Add ec2-user to docker group
usermod -a -G docker ec2-user

# Install Docker Compose
echo "Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Docker Buildx
echo "Installing Docker Buildx..."
mkdir -p ~/.docker/cli-plugins
curl -SL "https://github.com/docker/buildx/releases/download/v0.12.0/buildx-v0.12.0.linux-amd64" -o ~/.docker/cli-plugins/docker-buildx
chmod a+x ~/.docker/cli-plugins/docker-buildx

# Install Git
echo "Installing Git..."
yum install git -y

# Install AWS CLI
echo "Installing AWS CLI..."
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -q awscliv2.zip
./aws/install
rm -rf awscliv2.zip aws

# Install jq (JSON processor)
echo "Installing jq..."
yum install jq -y

# Configure Docker to start on boot
systemctl enable docker

# Get AWS account ID and login to ECR
echo "Logging into Amazon ECR..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
aws ecr get-login-password --region ${region} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${region}.amazonaws.com

# Clone repository
echo "Cloning DataPulse repository..."
cd /opt
git clone ${github_repo} DataPulse
cd DataPulse

# Checkout develop branch
echo "Checking out ${github_branch} branch..."
git checkout ${github_branch}

# Create .env file from template (if exists)
if [ -f .env.example ]; then
  cp .env.example .env
fi

# Start monitoring stack (Docker Compose)
echo "Starting monitoring stack..."
docker-compose up -d prometheus grafana loki promtail

# Configure cron for automatic updates
echo "Setting up automatic updates..."
cat >> /etc/cron.d/datapulse-updates << 'EOF'
# Update DataPulse every day at 2 AM
0 2 * * * root cd /opt/DataPulse && git pull origin ${github_branch} && docker-compose pull && docker-compose up -d
EOF
chmod 644 /etc/cron.d/datapulse-updates

# Create systemd service for application (optional)
echo "Creating systemd service for application..."
cat > /etc/systemd/system/datapulse.service << 'EOF'
[Unit]
Description=DataPulse Application
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=/opt/DataPulse
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

echo "=== Bootstrap Complete ==="
echo "Access the following services:"
echo "  - FastAPI: http://<public-ip>:8000"
echo "  - API Docs: http://<public-ip>:8000/docs"
echo "  - Grafana: http://<public-ip>:3000"
echo "  - Prometheus: http://<public-ip>:9090"
echo ""
echo "To enable auto-start: systemctl enable datapulse"
echo ""
echo "=== Rebooting to apply changes ==="
reboot
