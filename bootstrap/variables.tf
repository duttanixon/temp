variable "aws_region" {
    description = "AWS region to deploy resources"
    type = string
    default = "ap-northeast-1"
}

variable "state_bucket_name" {
    description = "Name of the s3 bucket for terraform state storage"
    type = string
    default = "ias_bucket"
}

variable "dynamodb_table_name" {
    description = "Name of the DynamoDB table for Terraform state locking"
    type = string
    default = "terraform-lock-table"
}

variable "aws_profile" {
  description = "AWS profile to use for authentication"
  type        = string
  default     = "cc-platform"
}