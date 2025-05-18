# CloudWatch Log Group for IoT devices metrics
resource "aws_cloudwatch_log_group" "iot_devices_metrics" {
  name              = "/iot-devices/metrics"
  retention_in_days = 7  # Adjust retention period as needed

  tags = {
    Environment = var.environment
    Description = "Log group for IoT devices metrics and health monitoring"
  }
}