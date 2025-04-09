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

module "iot" {
    source = "../../modules/iot"

    # Pass ant required variables to the module
    aws_region = var.aws_region
    environment = var.environment
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