variable "aws_region" {
    description = "AWS region to deploy resources"
    type        = string
}

variable "environment" {
    description="Environment name"
    type = string
}

variable "instance_id" {
  description = "ID of the EC2 instance to schedule"
  type        = string
}

variable "iot_devices_metrics_log_group" {
  description = "Name of the CloudWatch log group for IoT device metrics"
  type        = string
  default     = ""
}

variable "iot_devices_metrics_log_group_arn" {
  description = "ARN of the CloudWatch log group for IoT device metrics"
  type        = string
  default     = ""
}

variable "database_url" {
  description = "PostgreSQL database URL for the City Eye Lambda function"
  type        = string
  default     = ""
  sensitive   = true
}

variable "timestream_database_name" {
  description = "Name of the Timestream database for metrics"
  type        = string
  default     = ""
}

variable "timestream_raw_table_name" {
  description = "Name of the raw metrics table in Timestream"
  type        = string
  default     = ""
}

variable "timestream_hourly_table_name" {
  description = "Name of the hourly aggregated metrics table in Timestream"
  type        = string
  default     = ""
}

variable "timestream_daily_table_name" {
  description = "Name of the daily aggregated metrics table in Timestream"
  type        = string
  default     = ""
}