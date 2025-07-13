# modules/athena/variables.tf

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "edge_logs_bucket_name" {
  description = "Name of the S3 bucket containing edge logs"
  type        = string
}