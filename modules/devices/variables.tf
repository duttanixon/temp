variable "aws_region" {
    description = "AWS region to deploy resources"
    type        = string
}

variable "environment" {
    description="Environment name"
    type = string
}

variable "iot_device_metrics_user_name" {
    description = "iot devices user name"
    type = string
}

variable "edge_device_metrics_database_name" {
  description = "Name of the Timestream database"
  type        = string
}

variable "raw_table_name" {
  description = "Name of the raw metrics table"
  type        = string
}

variable "hourly_table_name" {
  description = "Name of the hourly aggregated metrics table"
  type        = string
}

variable "daily_table_name" {
  description = "Name of the daily aggregated metrics table"
  type        = string
}

variable "raw_memory_retention_hours" {
  description = "Memory store retention period in hours for raw metrics"
  type        = number
  default     = 2
}

variable "raw_magnetic_retention_days" {
  description = "Magnetic store retention period in days for raw metrics"
  type        = number
  default     = 14  # 14 days
}

variable "hourly_memory_retention_hours" {
  description = "Memory store retention period in hours for hourly metrics"
  type        = number
  default     = 2 
}

variable "hourly_magnetic_retention_days" {
  description = "Magnetic store retention period in days for hourly metrics"
  type        = number
  default     = 90  # 90 days
}

variable "daily_memory_retention_hours" {
  description = "Memory store retention period in hours for daily metrics"
  type        = number
  default     = 2
}

variable "daily_magnetic_retention_days" {
  description = "Magnetic store retention period in days for daily metrics"
  type        = number
  default     = 400  # ~13 months
}