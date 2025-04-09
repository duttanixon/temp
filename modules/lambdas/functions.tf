# Lambda functions  and related resources
resource "aws_lambda_function" "iot_data_processor_functions" {
    for_each = local.lambda_functions

    function_name       = each.value.function_name
    description         = each.value.description
    role                = aws_iam_role.lambda_execution_role.arn
    runtime             = each.value.runtime
    handler             = each.value.handler
    filename            = data.archive_file.lambda_archives[each.key].output_path
    source_code_hash    = data.archive_file.lambda_archives[each.key].output_base64sha256

    dynamic "environment" {
        for_each = length(each.value.environment_variables) > 0 ? [1] : []
        content {
            variables = each.value.environment_variables
        }
    }
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