variable "environment" {
    description = "Environment name"
    type        = string
}

# Database credential variables for Secrets Manager
variable "database_host" {
    description = "Database host"
    type        = string
}

variable "database_port" {
    description = "Database port"
    type        = number
    default     = 5432
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