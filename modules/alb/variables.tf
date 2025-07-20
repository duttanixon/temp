variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "domain_name" {
  description = "Domain name for the certificate"
  type        = string
}

variable "instance_id" {
  description = "EC2 instance ID to attach to the target group"
  type        = string
}