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
  layers              = [aws_lambda_layer_version.city_eye_dependencies.arn]

  # Increase timeout and memory for database operations
  timeout             = each.key == "city_eye" ? 30 : 10
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

# Lambda function for processing ioi devices metrics from CloudWatch
resource "aws_lambda_function" "iot_devices_metrics_processor" {
  function_name    = "${var.environment}-iot-devices-metrics-processor"
  description      = "Processes iot Devices metrics from CloudWatch and writes to Timestream"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "iot_devices_metrics_processor.lambda_handler"
  runtime          = "python3.9"
  timeout          = 180  # 3 minutes
  memory_size      = 256  # MB

  filename         = data.archive_file.iot_devices_metrics_processor_lambda.output_path
  source_code_hash = data.archive_file.iot_devices_metrics_processor_lambda.output_base64sha256

  layers           = [aws_lambda_layer_version.city_eye_dependencies.arn]

  environment {
    variables = {
      TIMESTREAM_DATABASE    = var.timestream_database_name
      TIMESTREAM_RAW_TABLE   = var.timestream_raw_table_name
    }
  }

  tags = {
    Name        = "${var.environment}-raspberry-pi-metrics-processor"
    Environment = var.environment
  }
}


resource "aws_lambda_function" "hourly_metrics_aggregator" {
  function_name    = "${var.environment}-hourly-metrics-aggregator"
  description      = "Aggregates iot devices metrics hourly and writes to Timestream"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "hourly_metrics_aggregator.lambda_handler"
  runtime          = "python3.9"
  timeout          = 300  # 5 minutes
  memory_size      = 256  # MB

  filename         = data.archive_file.hourly_metrics_aggregator_lambda.output_path
  source_code_hash = data.archive_file.hourly_metrics_aggregator_lambda.output_base64sha256

  environment {
    variables = {
      TIMESTREAM_DATABASE    = var.timestream_database_name
      TIMESTREAM_RAW_TABLE   = var.timestream_raw_table_name
      TIMESTREAM_HOURLY_TABLE = var.timestream_hourly_table_name
    }
  }

  tags = {
    Name        = "${var.environment}-hourly-metrics-aggregator"
    Environment = var.environment
  }
}

# Lambda function for daily metrics aggregation
resource "aws_lambda_function" "daily_metrics_aggregator" {
  function_name    = "${var.environment}-daily-metrics-aggregator"
  description      = "Aggregates Raspberry Pi metrics daily and writes to Timestream"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "daily_metrics_aggregator.lambda_handler"
  runtime          = "python3.9"
  timeout          = 300  # 5 minutes
  memory_size      = 256  # MB

  filename         = data.archive_file.daily_metrics_aggregator_lambda.output_path
  source_code_hash = data.archive_file.daily_metrics_aggregator_lambda.output_base64sha256

  environment {
    variables = {
      TIMESTREAM_DATABASE    = var.timestream_database_name
      TIMESTREAM_HOURLY_TABLE = var.timestream_hourly_table_name
      TIMESTREAM_DAILY_TABLE = var.timestream_daily_table_name
    }
  }

  tags = {
    Name        = "${var.environment}-daily-metrics-aggregator"
    Environment = var.environment
  }
}