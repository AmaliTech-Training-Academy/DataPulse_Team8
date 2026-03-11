# =====================================================
# Terraform Backend Configuration
# Uses S3 for remote state storage with DynamoDB for locking
# 
# IMPORTANT: After running terraform apply, uncomment the backend block
# and run: terraform init -migrate-state
# =====================================================

# DynamoDB Table for Terraform State Locking
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "datapulse-terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name        = "datapulse-terraform-locks"
    Environment = var.environment
  }
}

# S3 Bucket for Terraform State
resource "aws_s3_bucket" "terraform_state" {
  bucket = "datapulse-terraform-state-${var.aws_region}"

  tags = {
    Name        = "datapulse-terraform-state"
    Environment = var.environment
  }
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Server-Side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# -----------------------------------------------------------
# To enable S3 Backend (uncomment after first apply):
# -----------------------------------------------------------
# 
# In a separate file (e.g., terraform/backend-config.tf), add:
# 
# terraform {
#   backend "s3" {
#     bucket         = "datapulse-terraform-state-${var.aws_region}"
#     key            = "datapulse-${var.environment}/terraform.tfstate"
#     region         = var.aws_region
#     encrypt        = true
#     dynamodb_table = "datapulse-terraform-locks"
#   }
# }
# 
# Then run: terraform init -migrate-state

# Terraform Backend Outputs
output "terraform_state_bucket" {
  description = "S3 bucket for Terraform state"
  value       = aws_s3_bucket.terraform_state.id
}

output "terraform_lock_table" {
  description = "DynamoDB table for Terraform locks"
  value       = aws_dynamodb_table.terraform_locks.name
}

output "enable_s3_backend_instructions" {
  description = "Instructions to enable S3 backend"
  value       = <<-EOT
    To enable S3 backend after initial terraform apply:
    
    1. Create a new file terraform/backend-config.tf:
    
    terraform {
      backend "s3" {
        bucket         = "datapulse-terraform-state-${var.aws_region}"
        key            = "datapulse-${var.environment}/terraform.tfstate"
        region         = "${var.aws_region}"
        encrypt        = true
        dynamodb_table = "datapulse-terraform-locks"
      }
    }
    
    2. Run: terraform init -migrate-state
    
    Note: Variables cannot be used in terraform {} block.
    Replace ${var.aws_region} and ${var.environment} with actual values.
  EOT
  sensitive   = false
}
