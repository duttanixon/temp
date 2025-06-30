resource "aws_secretsmanager_secret" "platform_database_credentials" {
    name = "${var.environment}-platform_database_credentials"
    description             = "Database credentials for the platform"
    recovery_window_in_days = 7  # Allow recovery for 7 days after deletion

  tags = {
    Name        = "${var.environment}-platform-database-credentials"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Purpose     = "Database Credentials"
  }
}

# The secret version with the actual credentials
resource "aws_secretsmanager_secret_version" "platform_database_credentials" {
  secret_id = aws_secretsmanager_secret.platform_database_credentials.id
  
  secret_string = jsonencode({
    host     = var.database_host
    port     = var.database_port
    database = var.database_name
    username = var.database_username
    password = var.database_password
  })

  # Use lifecycle to prevent changes from destroying existing secret versions
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# IAM policy for accessing the database secret
resource "aws_iam_policy" "database_secret_access" {
  name        = "${var.environment}-database-secret-access-policy"
  description = "Policy for accessing database credentials from Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = aws_secretsmanager_secret.platform_database_credentials.arn
      }
    ]
  })
}

# Attach the secret access policy to the backend service user
resource "aws_iam_user_policy_attachment" "backend_database_secret_access" {
  user       = aws_iam_user.backend_service_user.name
  policy_arn = aws_iam_policy.database_secret_access.arn
}

# Attach the secret access policy to the backend service user
resource "aws_iam_user_policy_attachment" "device_database_secret_access" {
  user       = aws_iam_user.device_service_user.name
  policy_arn = aws_iam_policy.database_secret_access.arn
}