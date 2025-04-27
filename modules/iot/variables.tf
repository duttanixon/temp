variable "aws_region" {
    description = "AWS region to deploy resources"
    type        = string
}

variable "environment" {
    description="Environment name"
    type = string
}

variable "platform_backend_user_name" {
    description = "Backend user name"
    type = string
}