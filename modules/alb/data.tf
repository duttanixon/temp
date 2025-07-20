# Get default VPC
data "aws_vpc" "default" {
  default = true
}

# Get available subnets in the default VPC
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}