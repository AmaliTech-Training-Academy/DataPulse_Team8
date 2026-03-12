#!/bin/bash
# Script to create the required Secrets Manager secret for DataPulse

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed"
    exit 1
fi

# Check if required environment variables are set
if [ -z "$AWS_REGION" ]; then
    echo "AWS_REGION environment variable is not set"
    exit 1
fi

# Secret name (matching terraform/variables.tf default)
SECRET_NAME="datapulse/prod/credentials"

# Generate secure random passwords
POSTGRES_PASSWORD=$(openssl rand -base64 16)
GRAFANA_PASSWORD=$(openssl rand -base64 16)

# Create the secret JSON
SECRET_JSON=$(cat <<EOF
{
  "postgres_user": "datapulse_admin",
  "postgres_password": "${POSTGRES_PASSWORD}",
  "postgres_db": "datapulse_db",
  "grafana_admin_password": "${GRAFANA_PASSWORD}"
}
EOF
)

echo "Creating secret: ${SECRET_NAME}"
echo "Region: ${AWS_REGION}"

# Create the secret
aws secretsmanager create-secret \
    --name "${SECRET_NAME}" \
    --secret-string "${SECRET_JSON}" \
    --region "${AWS_REGION}"

if [ $? -eq 0 ]; then
    echo ""
    echo "Secret created successfully!"
    echo ""
    echo "IMPORTANT: Save these credentials securely:"
    echo "  Postgres User: datapulse_admin"
    echo "  Postgres Password: ${POSTGRES_PASSWORD}"
    echo "  Postgres DB: datapulse_db"
    echo "  Grafana Admin Password: ${GRAFANA_PASSWORD}"
    echo ""
    echo "You can retrieve them later with:"
    echo "  aws secretsmanager get-secret-value --secret-id ${SECRET_NAME} --region ${AWS_REGION}"
else
    echo "Failed to create secret"
    exit 1
fi
