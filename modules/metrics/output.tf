output "iot_device_cloudwatch_role_arn" {
  description = "ARN of the IAM role for Iot devices to access CloudWatch"
  value       = aws_iam_role.iot_devices_cloudwatch_role.arn
}