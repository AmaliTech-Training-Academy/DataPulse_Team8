#!/bin/bash
# =====================================================
# DataPulse — Full ECR Image Push & ECS Deploy Script
# Usage: ./deploy-to-ecr.sh [image_tag]
# Example: ./deploy-to-ecr.sh v1.0.0
# =====================================================
set -euo pipefail

# Disable provenance attestation to avoid broken pipe on multi-arch manifests
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain
export DOCKER_DEFAULT_PLATFORM=linux/arm64

# ── Configuration ────────────────────────────────────
REGION="${AWS_REGION:-eu-west-1}"
ACCOUNT_ID="384747604241"
ECR_BASE="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
IMAGE_TAG="${1:-latest}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ALB_DNS="datapulse-alb-dev-810866140.eu-west-1.elb.amazonaws.com"
CLUSTER="datapulse-dev"

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✓]${NC} $*"; }
info() { echo -e "${CYAN}[→]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
fail() { echo -e "${RED}[✗]${NC} $*"; exit 1; }

echo -e "\n${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  DataPulse ECR Push & ECS Deploy${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "  Region:  ${CYAN}${REGION}${NC}"
echo -e "  Account: ${CYAN}${ACCOUNT_ID}${NC}"
echo -e "  Tag:     ${CYAN}${IMAGE_TAG}${NC}"
echo -e "  ALB:     ${CYAN}http://${ALB_DNS}${NC}"
echo ""

# ── Step 0: Verify AWS credentials ──────────────────
info "Verifying AWS credentials..."
AWS_IDENTITY=$(aws sts get-caller-identity --output json 2>/dev/null) || fail "AWS credentials not valid. Export AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN."
CALLER_ACCOUNT=$(echo "$AWS_IDENTITY" | python3 -c "import sys,json; print(json.load(sys.stdin)['Account'])")
log "Authenticated as account: ${CALLER_ACCOUNT}"

# ── Step 1: ECR Login ────────────────────────────────
info "Logging into ECR (${REGION})..."
aws ecr get-login-password --region "${REGION}" | \
  docker login --username AWS --password-stdin "${ECR_BASE}"
log "ECR login successful"

# ── Step 2: Ensure CloudWatch log group exists ───────
info "Ensuring CloudWatch log group exists..."
aws logs create-log-group --log-group-name "/ecs/datapulse-backend" --region "${REGION}" 2>/dev/null || true
aws logs put-retention-policy --log-group-name "/ecs/datapulse-backend" --retention-in-days 7 --region "${REGION}" 2>/dev/null || true
log "CloudWatch log group ready"

# ── Step 3: Build backend image ──────────────────────
info "Building backend image..."
BACKEND_ECR="${ECR_BASE}/datapulse/backend"
docker build \
  --provenance=false \
  --sbom=false \
  -t "datapulse-backend:${IMAGE_TAG}" \
  -t "${BACKEND_ECR}:${IMAGE_TAG}" \
  -t "${BACKEND_ECR}:latest" \
  -f "${PROJECT_ROOT}/backend/Dockerfile" \
  "${PROJECT_ROOT}/backend"
log "Backend image built"

# ── Step 4: Build frontend image ─────────────────────
info "Building frontend image..."
FRONTEND_ECR="${ECR_BASE}/datapulse/frontend"
docker build \
  --provenance=false \
  --sbom=false \
  -t "datapulse-frontend:${IMAGE_TAG}" \
  -t "${FRONTEND_ECR}:${IMAGE_TAG}" \
  -t "${FRONTEND_ECR}:latest" \
  -f "${PROJECT_ROOT}/frontend/Dockerfile" \
  "${PROJECT_ROOT}/frontend"
log "Frontend image built"

# ── Step 5: Pull & tag monitoring images ─────────────
# ── Retry-push helper ────────────────────────────────
push_with_retry() {
  local tag="$1"
  local max_retries=5
  local attempt=1
  while [ $attempt -le $max_retries ]; do
    info "  Push attempt ${attempt}/${max_retries}: ${tag}"
    if docker push "${tag}"; then
      return 0
    fi
    attempt=$((attempt + 1))
    warn "  Push failed, retrying in 10s..."
    sleep 10
  done
  fail "  Push failed after ${max_retries} attempts: ${tag}"
}

info "Pulling Prometheus image..."
PROMETHEUS_ECR="${ECR_BASE}/datapulse/prometheus"
docker pull --platform linux/amd64 prom/prometheus:latest
docker tag prom/prometheus:latest "${PROMETHEUS_ECR}:latest"
log "Prometheus ready"

info "Pulling Grafana image..."
GRAFANA_ECR="${ECR_BASE}/datapulse/grafana"
docker pull --platform linux/amd64 grafana/grafana:latest
docker tag grafana/grafana:latest "${GRAFANA_ECR}:latest"
log "Grafana ready"

info "Pulling Loki image..."
LOKI_ECR="${ECR_BASE}/datapulse/loki"
docker pull --platform linux/amd64 grafana/loki:2.9.2
docker tag grafana/loki:2.9.2 "${LOKI_ECR}:latest"
log "Loki ready"

# ── Step 6: Push all images to ECR ───────────────────
echo ""
info "Pushing all images to ECR..."

push_image() {
  local name="$1"
  local repo="$2"
  local tag="$3"
  info "  Pushing ${name}:${tag}..."
  push_with_retry "${repo}:${tag}"
  if [[ "${tag}" != "latest" ]]; then
    push_with_retry "${repo}:latest"
  fi
  log "  ${name} pushed ✓"
}

push_image "backend"    "${BACKEND_ECR}"    "${IMAGE_TAG}"
push_image "frontend"   "${FRONTEND_ECR}"   "${IMAGE_TAG}"
push_image "prometheus" "${PROMETHEUS_ECR}" "latest"
push_image "grafana"    "${GRAFANA_ECR}"    "latest"
push_image "loki"       "${LOKI_ECR}"       "latest"

# ── Step 7: Register updated ECS Task Definition ─────
echo ""
info "Registering new ECS Task Definition for backend..."

TASK_DEF_ARN=$(aws ecs register-task-definition \
  --region "${REGION}" \
  --family "datapulse-backend" \
  --network-mode "awsvpc" \
  --requires-compatibilities "FARGATE" \
  --cpu "512" \
  --memory "1024" \
  --execution-role-arn "arn:aws:iam::${ACCOUNT_ID}:role/datapulse-ecs-task-execution-dev" \
  --task-role-arn "arn:aws:iam::${ACCOUNT_ID}:role/datapulse-ecs-task-dev" \
  --container-definitions "[
    {
      \"name\": \"backend\",
      \"image\": \"${BACKEND_ECR}:${IMAGE_TAG}\",
      \"essential\": true,
      \"portMappings\": [{\"containerPort\": 8000, \"hostPort\": 8000, \"protocol\": \"tcp\"}],
      \"environment\": [
        {\"name\": \"ENVIRONMENT\", \"value\": \"production\"},
        {\"name\": \"DATABASE_URL\", \"value\": \"postgresql://datapulse:datapulse123@datapulse-db:5432/datapulse\"}
      ],
      \"logConfiguration\": {
        \"logDriver\": \"awslogs\",
        \"options\": {
          \"awslogs-group\": \"/ecs/datapulse-backend\",
          \"awslogs-region\": \"${REGION}\",
          \"awslogs-stream-prefix\": \"ecs\"
        }
      },
      \"healthCheck\": {
        \"command\": [\"CMD-SHELL\", \"curl -sf http://localhost:8000/health || exit 1\"],
        \"interval\": 30,
        \"timeout\": 5,
        \"retries\": 3,
        \"startPeriod\": 60
      }
    }
  ]" \
  --query 'taskDefinition.taskDefinitionArn' \
  --output text)

log "Task Definition registered: ${TASK_DEF_ARN}"

# ── Step 8: Update ECS Service ───────────────────────
info "Updating ECS service (backend-blue) with new task definition..."
aws ecs update-service \
  --region "${REGION}" \
  --cluster "${CLUSTER}" \
  --service "datapulse-backend-blue-dev" \
  --task-definition "${TASK_DEF_ARN}" \
  --desired-count 1 \
  --force-new-deployment \
  --output json > /dev/null

log "ECS service update triggered"

# ── Step 9: Wait for service stability ──────────────
info "Waiting for ECS service to stabilize (this may take 2-5 minutes)..."
aws ecs wait services-stable \
  --region "${REGION}" \
  --cluster "${CLUSTER}" \
  --services "datapulse-backend-blue-dev"

log "ECS service is stable and running!"

# ── Step 10: Verify ALB health ───────────────────────
echo ""
info "Verifying ALB health check..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://${ALB_DNS}/health" --max-time 10 2>/dev/null || echo "000")
if [[ "${HTTP_STATUS}" == "200" ]]; then
  log "ALB health check passed! 🎉"
else
  warn "ALB returned HTTP ${HTTP_STATUS} — service may still be warming up (normal for first deploy)"
fi

# ── Step 11: Print summary ───────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  🚀 Deployment Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo ""
echo -e "  ${CYAN}Live API URL:${NC}    http://${ALB_DNS}"
echo -e "  ${CYAN}API Docs:${NC}        http://${ALB_DNS}/docs"
echo -e "  ${CYAN}Health Check:${NC}    http://${ALB_DNS}/health"
echo ""
echo -e "  ${CYAN}ECR Images Pushed:${NC}"
echo -e "    • ${BACKEND_ECR}:${IMAGE_TAG}"
echo -e "    • ${FRONTEND_ECR}:${IMAGE_TAG}"
echo -e "    • ${PROMETHEUS_ECR}:latest"
echo -e "    • ${GRAFANA_ECR}:latest"
echo -e "    • ${LOKI_ECR}:latest"
echo ""
echo -e "  ${YELLOW}ECS Cluster:${NC}     ${CLUSTER}"
echo -e "  ${YELLOW}Task Definition:${NC} ${TASK_DEF_ARN}"
echo ""
