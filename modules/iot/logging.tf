# IAM role for IoT Core logging

resource "aws_iam_role" "iot_logging_role" {
    name = "${var.environment}-iot-logging-role"

    assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Principal = {
          Service = "iot.amazonaws.com"
        }
        Effect = "Allow"
      }
    ]
  })
}

# IAM policy for IoT Core CloudWatch logging
resource "aws_iam_policy" "iot_logging_policy" {
    name = "${var.environment}-iot-logging-policy"
    description = "IAM policy for IoT Core CloudWatch logging"

    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
			    "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:PutMetricFilter",
                    "logs:PutRetentionPolicy",
                    "iot:GetLoggingOptions",
                    "iot:SetLoggingOptions",
                    "iot:SetV2LoggingOptions",
                    "iot:GetV2LoggingOptions",
                    "iot:SetV2LoggingLevel",
                    "iot:ListV2LoggingLevels",
                    "iot:DeleteV2LoggingLevel"   
                ],
        Resource = [
            "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:AWSIotLogsV2:*"
            # "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/iot/*:*",
            # "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/iot:*"
            ]
        }
        ]
    })
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "iot_logging_attachment" {
    role       = aws_iam_role.iot_logging_role.name
    policy_arn = aws_iam_policy.iot_logging_policy.arn
}

# Configure AWS IoT Core logging
resource "aws_iot_logging_options" "enable_iot_logging" {
    default_log_level = "INFO"
    role_arn          = aws_iam_role.iot_logging_role.arn
    disable_all_logs  = false
}

# # Optional: Create a dedicated log group for IoT Core
# resource "aws_cloudwatch_log_group" "iot_logs" {
#     name              = "/aws/iot/${var.environment}"
#     retention_in_days = 14
# }