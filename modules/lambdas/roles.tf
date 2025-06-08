# IAM role for lambda execution

resource "aws_iam_role" "lambda_execution_role" {
    name = "${var.environment}-iot-rule-lambda-role"

    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = "sts:AssumeRole"
                Effect = "Allow"
                Principal = {
                    Service = "lambda.amazonaws.com"
                }
            }
        ]
    })
}

# Policy to allow lambda to create CloudWatch logs
resource "aws_iam_policy" "lambda_logging" {
    name        = "${var.environment}-lambda-logging-policy"
    description = "IAM policy for logging from Lambda"

    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ]
                Effect      = "Allow"
                Resource    = [
                    "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.environment}-*",
                    "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.environment}-*:*"
                ]

            }
        ]


    })
}

# Attach lambda policy to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_logs" {
    role        = aws_iam_role.lambda_execution_role.name
    policy_arn  = aws_iam_policy.lambda_logging.arn
}


# IAM Role for the Lambda function
resource "aws_iam_role" "ec2_scheduler_role" {
  name = "${var.environment}-ec2-scheduler-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for EC2 control
resource "aws_iam_policy" "ec2_control_policy" {
  name        = "${var.environment}-ec2-control-policy"
  description = "IAM policy for starting and stopping EC2 instances"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ec2:StartInstances",
          "ec2:StopInstances",
          "ec2:DescribeInstances"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

# Policy to allow lambda to create CloudWatch logs
resource "aws_iam_policy" "lambda_logging_ec2" {
  name        = "${var.environment}-ec2-scheduler-logging-policy"
  description = "IAM policy for logging from Lambda"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.environment}-ec2-scheduler-*"
      }
    ]
  })
}


# Attach policies to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_logs_ec2" {
  role       = aws_iam_role.ec2_scheduler_role.name
  policy_arn = aws_iam_policy.lambda_logging_ec2.arn
}

resource "aws_iam_role_policy_attachment" "ec2_control" {
  role       = aws_iam_role.ec2_scheduler_role.name
  policy_arn = aws_iam_policy.ec2_control_policy.arn
}

# IAM policy for Timestream access
resource "aws_iam_policy" "lambda_timestream_policy" {
  name        = "${var.environment}-lambda-timestream-policy"
  description = "IAM policy for Lambda to access Timestream"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "timestream:WriteRecords",
          "timestream:DescribeTable",
          "timestream:ListTables",
          "timestream:DescribeDatabase",
          "timestream:ListDatabases",
          "timestream:Select",
          "timestream:Query"
        ]
        Resource = [
          "arn:aws:timestream:${var.aws_region}:${data.aws_caller_identity.current.account_id}:database/${var.timestream_database_name}",
          "arn:aws:timestream:${var.aws_region}:${data.aws_caller_identity.current.account_id}:database/${var.timestream_database_name}/table/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "timestream:DescribeEndpoints"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach Timestream policy to Lambda execution role
resource "aws_iam_role_policy_attachment" "lambda_timestream" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = aws_iam_policy.lambda_timestream_policy.arn
}


# Attach certificate bucket access policy to the backend service user
resource "aws_iam_user_policy_attachment" "timesteam_database_access_attachment" {
  user       = var.platform_backend_user_name
  policy_arn = aws_iam_policy.lambda_timestream_policy.arn
}