# IAM role for Raspberry Pi devices to access CloudWatch
resource "aws_iam_role" "iot_devices_cloudwatch_role" {
  name = "${var.environment}-iot-devices-cloudwatch-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/device/${var.environment}-device_service"
                  }
      }
    ]
  })
}

# CloudWatch access policy
resource "aws_iam_policy" "cloudwatch_iot_device_policy" {
  name        = "${var.environment}-cloudwatch-iot-device-policy"
  description = "Policy for Raspberry Pi devices to send logs and metrics to CloudWatch"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams",
          "cloudwatch:PutMetricData"
        ]
        Effect   = "Allow"
        Resource = [
                "arn:aws:logs:*:*:log-group:/iot-devices/metrics:*",
                "arn:aws:logs:*:*:log-group:/iot-devices/metrics:*:log-stream:*"
            ]
      }
    ]
  })
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "cloudwatch_iot_device_policy_attachment" {
  role       = aws_iam_role.iot_devices_cloudwatch_role.name
  policy_arn = aws_iam_policy.cloudwatch_iot_device_policy.arn
}


# Attach certificate bucket access policy to the device service user
resource "aws_iam_user_policy_attachment" "cloudwatch_iot_device_policy_attachment_to_user" {
  user       = var.iot_device_metrics_user_name
  policy_arn = aws_iam_policy.cloudwatch_iot_device_policy.arn
}