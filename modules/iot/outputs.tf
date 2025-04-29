# Now, let's update the outputs.tf in the modules/iot directory to include information about the logging configuration:
output "iot_logging_role_arn" {
    description = "ARN of the IAM role used for IoT Core logging"
    value       = aws_iam_role.iot_logging_role.arn
}

# output "iot_log_group_name" {
#     description = "Name of the CloudWatch log group for IoT Core logs"
#     value       = aws_cloudwatch_log_group.iot_logs.name
# }

output "device_policy_arn" {
  description = "The ARN of the IoT device communication policy"
  value       = aws_iot_policy.device_policy.arn
}

output "device_policy_name" {
  description = "The name of the IoT device communication policy"
  value       = aws_iot_policy.device_policy.name
}


# Add certificate bucket information to outputs
output "certificate_bucket_name" {
  description = "Name of the S3 bucket used for storing IoT certificates"
  value       = aws_s3_bucket.certificate_bucket.bucket
}