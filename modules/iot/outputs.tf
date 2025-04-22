# Now, let's update the outputs.tf in the modules/iot directory to include information about the logging configuration:
output "iot_logging_role_arn" {
    description = "ARN of the IAM role used for IoT Core logging"
    value       = aws_iam_role.iot_logging_role.arn
}

# output "iot_log_group_name" {
#     description = "Name of the CloudWatch log group for IoT Core logs"
#     value       = aws_cloudwatch_log_group.iot_logs.name
# }