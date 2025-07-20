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
    database_url = var.database_url
    api_base_url = var.api_base_url
    internal_api_key = var.internal_api_key
    iot_devices_metrics_log_group = module.metrics.iot_devices_metrics_log_group
    iot_devices_metrics_log_group_arn = module.metrics.iot_devices_metrics_log_group_arn
    timestream_database_name = module.metrics.timestream_database_name
    timestream_raw_table_name = module.metrics.timestream_raw_table_name
    platform_backend_user_name = module.common.backend_service_user_name

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
    database_host = var.database_host
    database_port = var.database_port
    database_name = var.database_name
    database_username = var.database_username
    database_password = var.database_password
}

module "metrics" {
    source =  "../../modules/devices"

    # Pass ant required variables to the module
    aws_region                          = var.aws_region
    environment                         = var.environment
    iot_device_metrics_user_name        = module.common.device_service_user_name
    platform_backend_user_name          = module.common.backend_service_user_name
    edge_device_metrics_database_name   = "edge-metrics"
    raw_table_name                      = "raw_metrics"
    hourly_table_name                   = "hourly_metrics"
    daily_table_name                    = "daily_metrics"
    raw_memory_retention_hours          = 1 
    raw_magnetic_retention_days         = 3   # 14 days
    hourly_memory_retention_hours       = 2   
    hourly_magnetic_retention_days      = 90   # 90 days
    daily_memory_retention_hours        = 2  
    daily_magnetic_retention_days       = 400  # ~13 months
}

# New Athena module for log analytics
module "athena" {
    source = "../../modules/athena"

    # Pass required variables to the module
    aws_region            = var.aws_region
    environment           = var.environment
    edge_logs_bucket_name = module.metrics.edge_log_bucket_name
}

module "alb" {
    source = "../../modules/alb"

    # Pass required variables to the module
    aws_region   = var.aws_region
    environment  = var.environment
    domain_name  = var.platform_domain
    instance_id  = module.ec2.instance_id

    # Ensure ALB is created after EC2
    depends_on = [module.ec2]
}