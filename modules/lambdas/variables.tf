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