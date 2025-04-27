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

