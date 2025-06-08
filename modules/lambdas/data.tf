locals {
    lambda_functions = {
        city_eye = {
            function_name   = "${var.environment}-city-eye-data-processor"
            handler         = "city_eye_data_processor.lambda_handler"
            runtime         = "python3.9"
            source_path     =  "${path.module}/files/city_eye_data_processor.py"
            description     = "Processes data from City Eye IoT devices"
            environment_variables = {
                ENVIRONMENT = var.environment
                DATABASE_URL = var.database_url
            }
        }
        # Add the new command response handler
        command_response = {
            function_name   = "${var.environment}-command-response-handler"
            handler         = "command_response_handler.lambda_handler"
            runtime         = "python3.9"
            source_path     = "${path.module}/files/command_response_handler.py"
            description     = "Handles device command responses"
            environment_variables = {
                ENVIRONMENT = var.environment
                API_BASE_URL = var.api_base_url
                INTERNAL_API_KEY = var.internal_api_key

            }
        }

        # Add function for each solution
    }

    iot_rules = {
        city_eye_rule = {
            name            =   "${var.environment}_device_data_lambda_rule"
            description     =   "Rule to process City Eye device data and trigger Lambda function"
            sql             =   "SELECT *, topic(2) AS client_id, topic(4) AS solution_name FROM 'devices/+/data/+'"
            lambda_key      =   "city_eye"
        }

        command_response_rule = {
            name            = "${var.environment}_device_command_response_rule"
            description     = "Rule to process device command responses and trigger Lambda function"
            sql             = "SELECT *, topic(2) AS client_id, topic(4) AS command_type FROM 'devices/+/command/+/response'"
            lambda_key      = "command_response"
        }
      
        # add rule for each solution
    }


}

# Create build directory if it doesn't exist
resource "null_resource" "create_build_dir" {
  provisioner "local-exec" {
    command = "mkdir -p ${path.module}/build"
  }
}

# copy lambda source file to build directory
resource "local_file" "lambda_sources_files" {
    for_each = local.lambda_functions

    content = file(each.value.source_path)
    filename = "${path.module}/build/${basename(each.value.source_path)}"
    depends_on = [null_resource.create_build_dir]

}

# create zip file for each lambda function
data "archive_file" "lambda_archives" {
    for_each    = local.lambda_functions

    type        = "zip"
    output_path = "${path.module}/build/${each.key}_function.zip"
    source_file = local_file.lambda_sources_files[each.key].filename
    depends_on  = [local_file.lambda_sources_files] 
}

# Archive files for Iot devices metrics Lambda functions
data "archive_file" "iot_devices_metrics_processor_lambda" {
  type        = "zip"
  output_path = "${path.module}/build/iot_devices_metrics_processor.zip"
  source {
    content  = file("${path.module}/files/iot_devices_metrics_processor.py")
    filename = "iot_devices_metrics_processor.py"
  }
  depends_on = [null_resource.create_build_dir]
}

data "archive_file" "hourly_metrics_aggregator_lambda" {
  type        = "zip"
  output_path = "${path.module}/build/hourly_metrics_aggregator.zip"
  source {
    content  = file("${path.module}/files/hourly_metrics_aggregator.py")
    filename = "hourly_metrics_aggregator.py"
  }
  depends_on = [null_resource.create_build_dir]
}

data "archive_file" "daily_metrics_aggregator_lambda" {
  type        = "zip"
  output_path = "${path.module}/build/daily_metrics_aggregator.zip"
  source {
    content  = file("${path.module}/files/daily_metrics_aggregator.py")
    filename = "daily_metrics_aggregator.py"
  }
  depends_on = [null_resource.create_build_dir]
}


  

data "archive_file" "ec2_scheduler_lambda" {
  type        = "zip"
  output_path = "${path.module}/build/ec2_scheduler_lambda.zip"
  source {
    content  = file("${path.module}/files/ec2_scheduler.py")
    filename = "ec2_scheduler.py"
  }
}


data "aws_caller_identity" "current" {}