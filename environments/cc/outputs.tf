output "backend_service_user_name" {
    description = "Name of the backend service user"
    value       = module.common.backend_service_user_name
}

output "backend_service_access_key_id" {
    description = "Name of the backend service user"
    value       = module.common.backend_service_access_key_id
}

output "backend_service_secret_access_key" {
    description = "Name of the backend service user"
    value       = module.common.backend_service_secret_access_key
    sensitive   = true
}

output "device_service_access_key_id" {
    description = "Name of the device service user"
    value       = module.common.device_service_access_key_id
}

output "device_service_secret_access_key" {
    description = "Name of the device service user"
    value       = module.common.device_service_secret_access_key
    sensitive   = true
}



output "account_id" {
    description = "Account ID"
    value = data.aws_caller_identity.current.account_id
}

output "device_certificate_policy_arn" {
    description = "ARN of the policy needed for device communication to IOT CORE"
    value = module.iot.device_policy_arn
}

output "device_certificate_policy_name" {
    description = "Name of the policy that is needed for device communication to IOT CORE"
    value = module.iot.device_policy_name
}

output "ec2_instance_ip_address" {
    description = "Dev instance IP address"
    value = module.ec2.instance_ip
}

# Add certificate bucket output
output "certificate_bucket_name" {
  description = "Name of the S3 bucket used for storing IoT certificates"
  value       = module.iot.certificate_bucket_name
}


output "iot_device_cloudwatch_role_arn" {
  description = "ARN of the IAM role for Iot devices to access CloudWatch"
  value       = module.metrics.iot_device_cloudwatch_role_arn
}

output "timestream_database_name" {
  description = "Name of the Timestream database for metrics"
  value       = module.metrics.timestream_database_name
}

output "timestream_raw_table_name" {
  description = "Name of the Timestream raw metrics table"
  value       = module.metrics.timestream_raw_table_name
}

output "timestream_hourly_table_name" {
  description = "Name of the Timestream hourly metrics table"
  value       = module.metrics.timestream_hourly_table_name
}

output "timestream_daily_table_name" {
  description = "Name of the Timestream daily metrics table"
  value       = module.metrics.timestream_daily_table_name
}