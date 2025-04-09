output "lambda_function_names" {
  description = "Names of the Lambda functions triggered by IoT Core"
  value       = { for k, v in aws_lambda_function.iot_data_processor_functions : k => v.function_name }
}

output "lambda_log_groups" {
  description = "CloudWatch Log Groups for the Lambda functions"
  value       = { for k, v in aws_lambda_function.iot_data_processor_functions : k => "/aws/lambda/${v.function_name}" }
}

output "iot_rule_names" {
  description = "Names of the IoT rules triggering the Lambda functions"
  value       = { for k, v in aws_iot_topic_rule.lambda_trigger_rules : k => v.name }
}