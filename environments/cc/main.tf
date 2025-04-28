provider "aws" {
    region = var.aws_region
    profile = var.aws_profile

    default_tags {
        tags = {
            Environment = var.environment
            ManagedBy = "Terraform"
        }
    }
}

data "aws_caller_identity" "current" {}

module "iot" {
    source = "../../modules/iot"

    # Pass ant required variables to the module
    aws_region = var.aws_region
    environment = var.environment
    platform_backend_user_name = module.common.backend_service_user_name
}

module "lambdas" {
    source =  "../../modules/lambdas"

    # Pass ant required variables to the module
    aws_region = var.aws_region
    environment = var.environment
    instance_id = module.ec2.instance_id
}

module "ec2" {
    source =  "../../modules/ec2"

    # Pass ant required variables to the module
    aws_region = var.aws_region
    environment = var.environment
}

module "common" {
    source =  "../../modules/common"

    # Pass ant required variables to the module
    environment = var.environment
}
