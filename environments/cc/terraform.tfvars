aws_region = "ap-northeast-1"
aws_profile = "cc-platform"
environment = "cc"

# Database configuration - this is sensitive and should ideally be managed via secrets
database_url = "postgresql+pg8000://ccadmin:qwerty12345@54.168.126.215/platformdb-dev"
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