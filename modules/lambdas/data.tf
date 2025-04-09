locals {
    lambda_functions = {
        city_eye = {
            function_name   = "${var.environment}-city-eye-data-processor"
            handler         = "city_eye_data_processor.lambda_handler"
            runtime         = "python3.12"
            source_path     =  "${path.module}/files/city_eye_data_processor.py"
            description     = "Processes data from City Eye IoT devices"
            environment_variables = {
                ENVIRONMENT = var.environment
            }
        }
        # Add function for each solution
    }

    iot_rules = {
        city_eye_rule = {
            name            =   "${var.environment}_device_data_lambda_rule"
            description     =   "Rule to process City Eye device data and trigger Lambda function"
            sql             =   "SELECT *, topic(2) AS client_id FROM 'devices/+/data/CityEyeSolution'"
            lambda_key      =   "city_eye"
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

data "aws_caller_identity" "current" {}