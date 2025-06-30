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

variable "database_host" {
    description = "Database host"
    type        = string
}

variable "database_port" {
    description = "Database port"
    type        = number
}

variable "database_name" {
    description = "Database name"
    type        = string
}

variable "database_username" {
    description = "Database username"
    type        = string
}

variable "database_password" {
    description = "Database password"
    type        = string
    sensitive   = true
}

variable "api_base_url" {
  description = "backend api url"
  type        = string
  default     = ""
}

variable "internal_api_key" {
  description = "internal api key for secured api access"
  type        = string
  default     = ""
  sensitive   = true
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
