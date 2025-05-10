# Lambda functions and related resources

# Lambda functions
resource "aws_lambda_function" "iot_data_processor_functions" {
  for_each = local.lambda_functions

  function_name       = each.value.function_name
  description         = each.value.description
  role                = aws_iam_role.lambda_execution_role.arn
  runtime             = each.value.runtime
  handler             = each.value.handler
  filename            = data.archive_file.lambda_archives[each.key].output_path
  source_code_hash    = data.archive_file.lambda_archives[each.key].output_base64sha256

  # Attach the layer to the city_eye function
  layers              = each.key == "city_eye" ? [aws_lambda_layer_version.city_eye_dependencies.arn] : []

  # Increase timeout and memory for database operations
  timeout             = each.key == "city_eye" ? 30 : 3
  memory_size         = each.key == "city_eye" ? 256 : 128

  dynamic "environment" {
    for_each = length(each.value.environment_variables) > 0 ? [1] : []
    content {
      variables = each.value.environment_variables
    }
  }
  # Make sure the lambda function is only created after the layer is ready
  depends_on = [
    aws_lambda_layer_version.city_eye_dependencies
  ]
}


# Lambda function to start EC2 instance
resource "aws_lambda_function" "ec2_start_function" {
  function_name    = "${var.environment}-ec2-scheduler-start"
  description      = "Function to start EC2 instance at 07:00 JST"
  role             = aws_iam_role.ec2_scheduler_role.arn
  handler          = "ec2_scheduler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 20
  filename         = data.archive_file.ec2_scheduler_lambda.output_path
  source_code_hash = data.archive_file.ec2_scheduler_lambda.output_base64sha256

  environment {
    variables = {
      INSTANCE_ID = var.instance_id
      ACTION      = "start"
    }
  }
}

# Lambda function to stop EC2 instance
resource "aws_lambda_function" "ec2_stop_function" {
  function_name    = "${var.environment}-ec2-scheduler-stop"
  description      = "Function to stop EC2 instance at 21:00 JST"
  role             = aws_iam_role.ec2_scheduler_role.arn
  handler          = "ec2_scheduler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 20
  filename         = data.archive_file.ec2_scheduler_lambda.output_path
  source_code_hash = data.archive_file.ec2_scheduler_lambda.output_base64sha256

  environment {
    variables = {
      INSTANCE_ID = var.instance_id
      ACTION      = "stop"
    }
  }
}