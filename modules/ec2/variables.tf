variable "aws_region" {
    description =  "AWS region to deploy resources"
    type        =   string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "availability_zone" {
  description = "Availability zone suffix (a, b, c, etc.)"
  type        = string
  default     = "a"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3a.medium"
}

variable "allowed_ssh_cidrs" {
  description = "List of CIDR blocks allowed to SSH into the instance"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "allowed_service_cidrs" {
  description = "List of CIDR blocks allowed to access services"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "data_volume_size" {
  description = "Size in GB for the data volume (for all services)"
  type        = number
  default     = 20
}

variable "engineer_ssh_keys" {
  description = "List of SSH public keys for the engineers"
  type        = list(string)
  default     = []
}