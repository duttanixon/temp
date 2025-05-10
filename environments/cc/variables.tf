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


# Lambda variables
variable "database_url" {
    description = "PostgreSQL database URL for the City Eye Lambda function"
    type = string
    sensitive = true
}

# EC2 module variables
variable "availability_zone" {
    description = "Availability zone suffix (a, b, c, etc.)"
    type        = string
}

variable "instance_type" {
    description = "EC2 instance type"
    type        = string
}

variable "allowed_ssh_cidrs" {
    description = "List of CIDR blocks allowed to SSH into the instance"
    type        = list(string)
}

variable "allowed_service_cidrs" {
    description = "List of CIDR blocks allowed to access services"
    type        = list(string)
}

variable "data_volume_size" {
    description = "Size in GB for the data volume (for all services)"
    type        = number
}

variable "engineer_ssh_keys" {
    description = "List of SSH public keys for the engineers"
    type        = list(string)
}
