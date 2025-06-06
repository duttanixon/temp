# Get the current AWS account ID
data "aws_caller_identity" "current" {}

# Use specific Ubuntu 24.04 LTS AMI
data "aws_ami" "ubuntu_24_04" {
    most_recent = true
    owners = ["099720109477"] # Canonical
    filter {
        name = "name"
        # This pattern now uses 'hvm-ssd*' to catch both gp2 and gp3 based images.
        values = ["ubuntu/images/hvm-ssd*/ubuntu-noble-24.04-amd64-server-*"]
    }
}