# =====================================================
# Lambda Scheduler for ECS Cost Optimization
# Starts ECS services at 7 AM and stops at 8 PM (Weekdays)
# =====================================================

# IAM Role for Lambda Scheduler
resource "aws_iam_role" "lambda_scheduler" {
  name = "datapulse-lambda-scheduler-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = {
    Environment = var.environment
  }
}

# IAM Policy for Lambda to manage ECS
resource "aws_iam_policy" "lambda_ecs_policy" {
  name        = "datapulse-lambda-ecs-policy-${var.environment}"
  description = "Policy for Lambda to start/stop ECS services"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecs:DescribeServices",
          "ecs:UpdateService",
          "ecs:ListTasks",
          "ecs:DescribeTasks"
        ]
        Resource = [
          "arn:aws:ecs:${var.aws_region}:*:service/${aws_ecs_cluster.main.name}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:DescribeClusters",
          "ecs:ListServices"
        ]
        Resource = aws_ecs_cluster.main.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:log-group:/aws/lambda/datapulse-scheduler-*"
      }
    ]
  })

  tags = {
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "lambda_ecs" {
  role       = aws_iam_role.lambda_scheduler.name
  policy_arn = aws_iam_policy.lambda_ecs_policy.arn
}

# Lambda Function to START ECS Services
resource "aws_lambda_function" "ecs_start" {
  filename      = "${path.module}/scripts/lambda_start.zip"
  function_name = "datapulse-ecs-start-${var.environment}"
  role          = aws_iam_role.lambda_scheduler.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 300

  environment {
    variables = {
      CLUSTER_NAME  = aws_ecs_cluster.main.name
      SERVICES      = "${aws_ecs_service.backend_blue.name},${aws_ecs_service.backend_green.name}"
      DESIRED_COUNT = "2"
      ACTION        = "START"
    }
  }

  # Use inline code if zip not available
  # This is a placeholder - actual Lambda code should be provided
  source_code_hash = fileexists("${path.module}/scripts/lambda_start.zip") ? filebase64sha256("${path.module}/scripts/lambda_start.zip") : ""

  # For demo purposes, use a placeholder (will work with proper zip file)
  package_type = "Zip"

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

# Lambda Function to STOP ECS Services
resource "aws_lambda_function" "ecs_stop" {
  filename      = "${path.module}/scripts/lambda_stop.zip"
  function_name = "datapulse-ecs-stop-${var.environment}"
  role          = aws_iam_role.lambda_scheduler.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 300

  environment {
    variables = {
      CLUSTER_NAME  = aws_ecs_cluster.main.name
      SERVICES      = "${aws_ecs_service.backend_blue.name},${aws_ecs_service.backend_green.name}"
      DESIRED_COUNT = "0"
      ACTION        = "STOP"
    }
  }

  source_code_hash = fileexists("${path.module}/scripts/lambda_stop.zip") ? filebase64sha256("${path.module}/scripts/lambda_stop.zip") : ""

  package_type = "Zip"

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

# CloudWatch Log Groups for Lambda
resource "aws_cloudwatch_log_group" "lambda_start" {
  name              = "/aws/lambda/datapulse-ecs-start-${var.environment}"
  retention_in_days = 7

  tags = {
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "lambda_stop" {
  name              = "/aws/lambda/datapulse-ecs-stop-${var.environment}"
  retention_in_days = 7

  tags = {
    Environment = var.environment
  }
}

# EventBridge Rule - Weekday Morning (7 AM)
resource "aws_cloudwatch_event_rule" "weekday_morning" {
  name                = "datapulse-ecs-start-${var.environment}"
  description         = "Start ECS services at 7 AM on weekdays"
  schedule_expression = "cron(0 7 ? * MON-FRI *)"

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

# EventBridge Rule - Weekday Evening (8 PM)
resource "aws_cloudwatch_event_rule" "weekday_evening" {
  name                = "datapulse-ecs-stop-${var.environment}"
  description         = "Stop ECS services at 8 PM on weekdays"
  schedule_expression = "cron(0 20 ? * MON-FRI *)"

  tags = {
    Environment = var.environment
    Project     = "DataPulse"
  }
}

# EventBridge Target - Start Lambda
resource "aws_cloudwatch_event_target" "ecs_start" {
  rule      = aws_cloudwatch_event_rule.weekday_morning.name
  target_id = "datapulse-ecs-start"
  arn       = aws_lambda_function.ecs_start.arn
}

# EventBridge Target - Stop Lambda
resource "aws_cloudwatch_event_target" "ecs_stop" {
  rule      = aws_cloudwatch_event_rule.weekday_evening.name
  target_id = "datapulse-ecs-stop"
  arn       = aws_lambda_function.ecs_stop.arn
}

# Permission for EventBridge to invoke Lambda
resource "aws_lambda_permission" "allow_eventbridge_start" {
  statement_id  = "AllowExecutionFromEventBridgeStart"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ecs_start.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.weekday_morning.arn
}

resource "aws_lambda_permission" "allow_eventbridge_stop" {
  statement_id  = "AllowExecutionFromEventBridgeStop"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ecs_stop.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.weekday_evening.arn
}

# Lambda Scheduler Outputs
output "ecs_start_function_name" {
  description = "ECS Start Lambda function name"
  value       = aws_lambda_function.ecs_start.function_name
}

output "ecs_stop_function_name" {
  description = "ECS Stop Lambda function name"
  value       = aws_lambda_function.ecs_stop.function_name
}

output "weekday_morning_rule_arn" {
  description = "EventBridge rule ARN for morning start"
  value       = aws_cloudwatch_event_rule.weekday_morning.arn
}

output "weekday_evening_rule_arn" {
  description = "EventBridge rule ARN for evening stop"
  value       = aws_cloudwatch_event_rule.weekday_evening.arn
}

output "estimated_cost_savings" {
  description = "Estimated monthly cost savings (~60%)"
  value       = "~60% (ECS running 11 hours/day on weekdays only)"
}
