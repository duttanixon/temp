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