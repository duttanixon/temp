# Get the current AWS account ID
data "aws_caller_identity" "current" {}

# Use specific Ubuntu 24.04 LTS AMI
data "aws_ami" "ubuntu_24_04" {
    most_recent = true
    owners = ["099720109477"] # Canonical

    filter {
        name = "image-id"
        values = ["ami-026c39f4021df9abe"]
    }
}