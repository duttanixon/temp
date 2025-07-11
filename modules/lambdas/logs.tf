resource "aws_cloudwatch_log_group" "command_response_handler_logs" {
  name              = "/aws/lambda/${var.environment}-command-response-handler"
  retention_in_days = 14

  tags = {
    Environment = var.environment
    Description = "Log group for IoT command response handler Lambda function"
    ManagedBy   = "Terraform"
  }
}

resource "aws_cloudwatch_log_group" "shadow_response_handler_logs" {
  name              = "/aws/lambda/${var.environment}-shadow-response-handler"
  retention_in_days = 14

  tags = {
    Environment = var.environment
    Description = "Log group for IoT shadow response handler Lambda function"
    ManagedBy   = "Terraform"
  }
}

resource "aws_cloudwatch_log_group" "lwt_handler_logs" {
  name              = "/aws/lambda/${var.environment}-device-last-will-testament"
  retention_in_days = 7

  tags = {
    Environment = var.environment
    Description = "Log group for IoT device last will and testament handler Lambda function"
    ManagedBy   = "Terraform"
  }
}