aws_region = "ap-northeast-1"
aws_profile = "cc-platform"
environment = "cc"

# Database configuration - this is sensitive and should ideally be managed via secrets
database_url = "postgresql+pg8000://ccadmin:qwerty12345@54.168.126.215/platformdb-dev"
api_base_url = "http://54.168.126.215:8000/api/v1"
internal_api_key = "k-TzDzlJew9s3Z_NXJprY4cwgL0IeiaQeZ8fHVx2N8M"
database_host = "54.168.126.215"
database_port = 5432
database_name = "platformdb-dev"
database_username = "ccadmin"
database_password = "qwerty12345"  # Sensitive information, should be managed securely

# In production, use terraform-apply with -var or environment variables instead of hardcoding here


# EC2 specific settings
availability_zone = "a"
instance_type = "t3a.medium"
allowed_ssh_cidrs = ["0.0.0.0/0"]  
allowed_service_cidrs = ["0.0.0.0/0"]  
data_volume_size = 20

# Add your engineers' SSH public keys here
engineer_ssh_keys = [
  "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC... engineer1@example.com",
  "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC... engineer2@example.com",
  "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC... engineer3@example.com",
  "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC... engineer4@example.com"
]