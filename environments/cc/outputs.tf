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

output "device_common_group_policy_arn" {
    description = "ARN of the policy needed for device communication to IOT CORE"
    value = module.iot.device_common_group_policy_arn
}

output "device_common_group_policy_name" {
    description = "Name of the policy that is needed for device communication to IOT CORE"
    value = module.iot.device_common_group_policy_name
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

output "edge_log_bucket_name" {
  description = "Name of the S3 bucket for edge logs"
  value       = module.metrics.edge_log_bucket_name
}

# Athena outputs
output "athena_workgroup_name" {
  description = "Name of the Athena workgroup for edge analytics"
  value       = module.athena.athena_workgroup_name
}

output "athena_database_name" {
  description = "Name of the Glue catalog database for edge analytics"
  value       = module.athena.glue_database_name
}

output "athena_results_bucket" {
  description = "S3 bucket for Athena query results"
  value       = module.athena.athena_results_bucket_name
}

output "athena_tables" {
  description = "Names of the Athena tables created"
  value = {
    application_logs = module.athena.application_logs_table_name
  }
}

output "athena_named_queries" {
  description = "Named queries created in Athena"
  value       = module.athena.athena_queries
}

# Superset outputs (replacing QuickSight)
output "superset_athena_user_arn" {
  description = "ARN of the IAM user for Superset to access Athena"
  value       = module.athena.superset_athena_user_arn
}

output "superset_athena_user_name" {
  description = "Name of the IAM user for Superset to access Athena"
  value       = module.athena.superset_athena_user_name
}

output "superset_athena_role_arn" {
  description = "ARN of the IAM role for Superset to access Athena"
  value       = module.athena.superset_athena_role_arn
}

output "superset_athena_access_key_id" {
  description = "Access key ID for Superset to access Athena"
  value       = module.athena.superset_athena_access_key_id
}

output "superset_athena_secret_access_key" {
  description = "Secret access key for Superset to access Athena"
  value       = module.athena.superset_athena_secret_access_key
  sensitive   = true
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.alb.alb_dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = module.alb.alb_zone_id
}

output "acm_certificate_validation_records" {
  description = "DNS validation records for ACM certificate - Add these to your DNS provider"
  value       = module.alb.acm_certificate_validation_records
}

output "platform_url" {
  description = "URL to access the platform"
  value       = "https://${var.platform_domain}"
}

# output "ses_user_access_key_id" {
#   description = "Access key ID for the SES user"
#   value       = module.common.ses_user_access_key_id
# }

# output "ses_user_secret_access_key" {
#   description = "Secret access key for the SES user"
#   value       = module.common.ses_user_secret_access_key
#   sensitive   = true
# }

output "ses_dkim_dns_records" {
  description = "DKIM CNAME records to add to your DNS provider (Sakura Cloud)"
  value = {
    for token in module.common.ses_dkim_tokens :
    "${token}._domainkey.cybercore.co.jp" => "${token}.dkim.amazonses.com"
  }
}

output "ses_smtp_user_access_key_id" {
  description = "Access key ID for the SES SMTP user (SMTP Username)"
  value       = module.common.ses_smtp_user_access_key_id
}

output "ses_smtp_password" {
  description = "The generated SMTP password for the SES user."
  value       = module.common.ses_smtp_password
  sensitive   = true
}