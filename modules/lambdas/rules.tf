# IoT Rules that trigger lambda functions

resource "aws_iot_topic_rule" "lambda_trigger_rules" {
    for_each = local.iot_rules

    name            = each.value.name
    description     = each.value.description
    enabled         = true

    sql             = each.value.sql
    sql_version     = "2016-03-23"

    lambda {
        function_arn =  aws_lambda_function.iot_data_processor_functions[each.value.lambda_key].arn
    }

}

# Permission to allow IoT to invoke the Lambda functions
resource "aws_lambda_permission" "allow_iot_invocations" {
    for_each        = local.iot_rules
    statement_id    = "AllowExecutionFromIoT_${each.key}"
    action          = "lambda:InvokeFunction"
    function_name   = aws_lambda_function.iot_data_processor_functions[each.value.lambda_key].function_name
    principal       = "iot.amazonaws.com"
    source_arn      =  aws_iot_topic_rule.lambda_trigger_rules[each.key].arn
}

# CloudWatch Event Rule for starting EC2 instance at 07:00 JST (22:00 UTC previous day)
resource "aws_cloudwatch_event_rule" "ec2_start_rule" {
  name                = "${var.environment}-ec2-start-rule"
  description         = "Start EC2 instance at 07:00 JST every day"
  schedule_expression = "cron(0 22 ? * * *)"  # UTC time (22:00 UTC = 07:00 JST next day)
}

# CloudWatch Event Rule for stopping EC2 instance at 21:00 JST (12:00 UTC)
resource "aws_cloudwatch_event_rule" "ec2_stop_rule" {
  name                = "${var.environment}-ec2-stop-rule"
  description         = "Stop EC2 instance at 21:00 JST every day"
  schedule_expression = "cron(00 12 ? * * *)"  # UTC time (12:00 UTC = 21:00 JST)
}

# CloudWatch Event Target for starting EC2 instance
resource "aws_cloudwatch_event_target" "ec2_start_target" {
  rule      = aws_cloudwatch_event_rule.ec2_start_rule.name
  target_id = "StartEC2Instance"
  arn       = aws_lambda_function.ec2_start_function.arn
}

# CloudWatch Event Target for stopping EC2 instance
resource "aws_cloudwatch_event_target" "ec2_stop_target" {
  rule      = aws_cloudwatch_event_rule.ec2_stop_rule.name
  target_id = "StopEC2Instance"
  arn       = aws_lambda_function.ec2_stop_function.arn
}

# Lambda permission for CloudWatch to invoke start function
resource "aws_lambda_permission" "allow_cloudwatch_to_start_ec2" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ec2_start_function.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ec2_start_rule.arn
}

# Lambda permission for CloudWatch to invoke stop function
resource "aws_lambda_permission" "allow_cloudwatch_to_stop_ec2" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ec2_stop_function.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ec2_stop_rule.arn
}

# CloudWatch Log Subscription Filter for Raspberry Pi metrics
resource "aws_cloudwatch_log_subscription_filter" "iot_device_metrics_filter" {
  name            = "${var.environment}-iot-devices-metrics-filter"
  log_group_name  = var.iot_devices_metrics_log_group
  filter_pattern  = ""  # Empty pattern to match all logs
  destination_arn = aws_lambda_function.iot_devices_metrics_processor.arn
}

# Lambda permission for CloudWatch Logs to invoke metrics processor
resource "aws_lambda_permission" "allow_cloudwatch_to_invoke_metrics_processor" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.iot_devices_metrics_processor.function_name
  principal     = "logs.${var.aws_region}.amazonaws.com"
  source_arn    = "${var.iot_devices_metrics_log_group_arn}:*"
}


# CloudWatch Events Rule for hourly aggregation
resource "aws_cloudwatch_event_rule" "hourly_aggregation_rule" {
  name                = "${var.environment}-hourly-metrics-aggregation"
  description         = "Trigger hourly metrics aggregation"
  schedule_expression = "cron(0 * * * ? *)"  # Run at the top of every hour
  
  tags = {
    Environment = var.environment
  }
}

# CloudWatch Events Target for hourly aggregation
resource "aws_cloudwatch_event_target" "hourly_aggregation_target" {
  rule      = aws_cloudwatch_event_rule.hourly_aggregation_rule.name
  target_id = "HourlyMetricsAggregator"
  arn       = aws_lambda_function.hourly_metrics_aggregator.arn
}

# Lambda permission for CloudWatch Events to invoke hourly aggregator
resource "aws_lambda_permission" "allow_events_to_invoke_hourly_aggregator" {
  statement_id  = "AllowExecutionFromCloudWatchEvents"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.hourly_metrics_aggregator.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.hourly_aggregation_rule.arn
}

# CloudWatch Events Rule for daily aggregation
resource "aws_cloudwatch_event_rule" "daily_aggregation_rule" {
  name                = "${var.environment}-daily-metrics-aggregation"
  description         = "Trigger daily metrics aggregation"
  schedule_expression = "cron(0 0 * * ? *)"  # Run at midnight UTC every day
  
  tags = {
    Environment = var.environment
  }
}

# CloudWatch Events Target for daily aggregation
resource "aws_cloudwatch_event_target" "daily_aggregation_target" {
  rule      = aws_cloudwatch_event_rule.daily_aggregation_rule.name
  target_id = "DailyMetricsAggregator"
  arn       = aws_lambda_function.daily_metrics_aggregator.arn
}

# Lambda permission for CloudWatch Events to invoke daily aggregator
resource "aws_lambda_permission" "allow_events_to_invoke_daily_aggregator" {
  statement_id  = "AllowExecutionFromCloudWatchEvents"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.daily_metrics_aggregator.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_aggregation_rule.arn
}

