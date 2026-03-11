#!/bin/bash
# =====================================================
# DataPulse ECS Blue-Green Deployment Script
# =====================================================

set -e

# Configuration
REGION="${AWS_REGION:-eu-west-1}"
CLUSTER_NAME="datapulse-${ENVIRONMENT:-dev}"
SERVICE_BLUE="datapulse-backend-blue-${ENVIRONMENT:-dev}"
SERVICE_GREEN="datapulse-backend-green-${ENVIRONMENT:-dev}"
ECR_REPO="datapulse/backend"
ALB_LISTENER_ARN="${ALB_LISTENER_ARN}"
TARGET_GROUP_BLUE_ARN="${TARGET_GROUP_BLUE_ARN}"
TARGET_GROUP_GREEN_ARN="${TARGET_GROUP_GREEN_ARN}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}DataPulse Blue-Green Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Check for required variables
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}Error: AWS_ACCOUNT_ID not set${NC}"
    exit 1
fi

# Parse image tag from argument or use default
IMAGE_TAG="${1:-latest}"
IMAGE="${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPO}:${IMAGE_TAG}"

echo -e "${YELLOW}Deploying: ${IMAGE}${NC}"
echo -e "Environment: ${ENVIRONMENT:-dev}"
echo -e "Cluster: ${CLUSTER_NAME}"

# Step 1: Register new task definition
echo -e "\n${YELLOW}Step 1: Registering new task definition...${NC}"

# Get the current task definition family
TASK_FAMILY="datapulse-backend"
TASK_DEF_ARN=$(aws ecs register-task-definition \
    --family "$TASK_FAMILY" \
    --network-mode "awsvpc" \
    --requires-compatibilities "FARGATE" \
    --cpu "512" \
    --memory "1024" \
    --execution-role-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:role/datapulse-ecs-task-execution-${ENVIRONMENT:-dev}" \
    --task-role-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:role/datapulse-ecs-task-${ENVIRONMENT:-dev}" \
    --container-definitions '[{"name":"backend","image":"'"$IMAGE"'","essential":true,"portMappings":[{"containerPort":8000,"hostPort":8000,"protocol":"tcp"}],"logConfiguration":{"logDriver":"awslogs","options":{"awslogs-group":"/ecs/datapulse-'"${ENVIRONMENT:-dev}"'","awslogs-region":"'"$REGION"'","awslogs-stream-prefix":"ecs"}}}]' \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

echo -e "${GREEN}New task definition: ${TASK_DEF_ARN}${NC}"

# Step 2: Deploy to green environment (canary)
echo -e "\n${YELLOW}Step 2: Deploying to green environment...${NC}"

# Update green service with new task definition
aws ecs update-service \
    --cluster "$CLUSTER_NAME" \
    --service "$SERVICE_GREEN" \
    --task-definition "$TASK_DEF_ARN" \
    --desired-count 1 \
    --force-new-deployment

echo -e "${GREEN}Green deployment initiated${NC}"

# Wait for green service to stabilize
echo -e "${YELLOW}Waiting for green service to stabilize...${NC}"
aws ecs wait services-stable \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_GREEN"

echo -e "${GREEN}Green environment is healthy!${NC}"

# Step 3: Traffic shift (gradual or immediate)
TRAFFIC_SHIFT_METHOD="${3:-immediate}"  # immediate or gradual

if [ "$TRAFFIC_SHIFT_METHOD" = "gradual" ]; then
    echo -e "\n${YELLOW}Step 3: Gradual traffic shift to green...${NC}"
    
    # Shift 25% traffic first
    echo "Shifting 25% traffic..."
    aws elbv2 modify-listener \
        --listener-arn "$ALB_LISTENER_ARN" \
        --default-actions '[{"Type":"forward","TargetGroupArn":"'"$TARGET_GROUP_GREEN_ARN"'","ForwardConfig":{"TargetGroups":[{"TargetGroupArn":"'"$TARGET_GROUP_BLUE_ARN"'","Weight":75},{"TargetGroupArn":"'"$TARGET_GROUP_GREEN_ARN"'","Weight":25}]}}]'
    
    sleep 30
    
    # Shift 50% traffic
    echo "Shifting 50% traffic..."
    aws elbv2 modify-listener \
        --listener-arn "$ALB_LISTENER_ARN" \
        --default-actions '[{"Type":"forward","TargetGroupArn":"'"$TARGET_GROUP_GREEN_ARN"'","ForwardConfig":{"TargetGroups":[{"TargetGroupArn":"'"$TARGET_GROUP_BLUE_ARN"'","Weight":50},{"TargetGroupArn":"'"$TARGET_GROUP_GREEN_ARN"'","Weight":50}]}}]'
    
    sleep 30
    
    # Shift 100% traffic to green
    echo "Shifting 100% traffic to green..."
    aws elbv2 modify-listener \
        --listener-arn "$ALB_LISTENER_ARN" \
        --default-actions '[{"Type":"forward","TargetGroupArn":"'"$TARGET_GROUP_GREEN_ARN"'","ForwardConfig":{"TargetGroups":[{"TargetGroupArn":"'"$TARGET_GROUP_BLUE_ARN"'","Weight":0},{"TargetGroupArn":"'"$TARGET_GROUP_GREEN_ARN"'","Weight":100}]}}]'
else
    echo -e "\n${YELLOW}Step 3: Immediate traffic shift to green...${NC}"
    aws elbv2 modify-listener \
        --listener-arn "$ALB_LISTENER_ARN" \
        --default-actions '[{"Type":"forward","TargetGroupArn":"'"$TARGET_GROUP_GREEN_ARN"'"}]'
fi

# Step 4: Scale down blue environment
echo -e "\n${YELLOW}Step 4: Scaling down blue environment...${NC}"
aws ecs update-service \
    --cluster "$CLUSTER_NAME" \
    --service "$SERVICE_BLUE" \
    --desired-count 0

echo -e "${GREEN}Blue environment scaled down${NC}"

# Step 5: Verify deployment
echo -e "\n${YELLOW}Step 5: Verifying deployment...${NC}"
aws ecs describe-services \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_BLUE" "$SERVICE_GREEN" \
    --query 'services[*].{Name:serviceName,Running:runningCount,Desired:desiredCount}'

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "New version deployed to green environment"
echo -e "Traffic has been shifted to green"
echo -e "Blue environment has been scaled to 0"
