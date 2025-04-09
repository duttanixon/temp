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
                Resource    = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.environment}-*"

            }
        ]


    })
}

# Attach lambda policy to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_logs" {
    role        = aws_iam_role.lambda_execution_role.name
    policy_arn  = aws_iam_policy.lambda_logging.arn
}