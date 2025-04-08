variable "aws_region" {
    description = "AWS region to deploy resources"
    type = string
    default = "ap-northeast-1"
}

variable "aws_profile" {
    description = "AWS profile to use for authentication"
    type = string
    default = "cc-platform"
}

variable "environment" {
    description="Environment name"
    type = string
}