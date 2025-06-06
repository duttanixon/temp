output "iot_device_cloudwatch_role_arn" {
  description = "ARN of the IAM role for Iot devices to access CloudWatch"
  value       = aws_iam_role.iot_devices_cloudwatch_role.arn
}

output "timestream_database_name" {
  description = "Name of the Timestream database"
  value       = aws_timestreamwrite_database.metrics_db.database_name
}

output "timestream_raw_table_name" {
  description = "Name of the raw metrics table"
  value       = aws_timestreamwrite_table.raw_metrics.table_name
}

output "timestream_hourly_table_name" {
  description = "Name of the hourly metrics table"
  value       = aws_timestreamwrite_table.hourly_metrics.table_name
}

output "timestream_daily_table_name" {
  description = "Name of the daily metrics table"
  value       = aws_timestreamwrite_table.daily_metrics.table_name
}

output "timestream_database_arn" {
  description = "ARN of the Timestream database"
  value       = aws_timestreamwrite_database.metrics_db.arn
}

output "timestream_raw_table_arn" {
  description = "ARN of the raw metrics table"
  value       = aws_timestreamwrite_table.raw_metrics.arn
}

output "timestream_hourly_table_arn" {
  description = "ARN of the hourly metrics table"
  value       = aws_timestreamwrite_table.hourly_metrics.arn
}

output "timestream_daily_table_arn" {
  description = "ARN of the daily metrics table"
  value       = aws_timestreamwrite_table.daily_metrics.arn
}

output "iot_devices_metrics_log_group" {
  description = "Name of the CloudWatch log group for IoT devices metrics"
  value       = aws_cloudwatch_log_group.iot_devices_metrics.name
}

output "iot_devices_metrics_log_group_arn" {
  description = "ARN of the CloudWatch log group for IoT devices metrics"
  value       = aws_cloudwatch_log_group.iot_devices_metrics.arn
}