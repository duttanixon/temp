# IAM User for managing IoT thing groups and policies
resource "aws_iam_user" "backend_service_user" {
    name = "${var.environment}-backend_service"
    path = "/backend/"

    tags = {
        Description = "User for managing Backend API"
        Environment = var.environment
    }
}

# Create access key for the backend service_user
resource "aws_iam_access_key" "backend_service_key" {
    user = aws_iam_user.backend_service_user.name
}


# IAM User for managing device connection to cloud such as Health monitoring metrics
resource "aws_iam_user" "device_service_user" {
    name = "${var.environment}-device_service"
    path = "/device/"

    tags = {
        Description = "User for managing Device connection to cloud"
        Environment = var.environment
    }
}

# Create access key for the device service user
resource "aws_iam_access_key" "device_service_key" {
    user = aws_iam_user.device_service_user.name
}