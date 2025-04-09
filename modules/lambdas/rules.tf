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