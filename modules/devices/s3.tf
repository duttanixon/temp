resource "aws_s3_bucket" "capture_image_bucket" {
    bucket = "${var.environment}-captured-images"

    tags = {
        Name = "${var.environment}-capture-images"
    }
}

# S3 bucket for storing logs
resource "aws_s3_bucket" "edge_logs" {
  bucket = "${var.environment}-edge-analytics-logs-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name        = "${var.environment}-edge-logs"
    Environment = var.environment
  }
}

# S3 bucket lifecycle policy to optimize costs
resource "aws_s3_bucket_lifecycle_configuration" "edge_logs_lifecycle" {
  bucket = aws_s3_bucket.edge_logs.id

  rule {
    id     = "transition-old-logs"
    status = "Enabled"

    # Move to Glacier after 90 days
    transition {
      days          = 3
      storage_class = "GLACIER"
    }

    # Delete after 365 days (optional - adjust based on your retention needs)
    expiration {
      days = 7
    }
  }
}

# S3 bucket versioning
resource "aws_s3_bucket_versioning" "edge_logs_versioning" {
  bucket = aws_s3_bucket.edge_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}



resource "aws_s3_bucket_versioning" "capture_image_bucket_versioning" {
    bucket  =  aws_s3_bucket.capture_image_bucket.id

    versioning_configuration {
        status = "Enabled"
    }
}

resource "aws_iam_policy" "s3_access_to_image_bucket" {
  name        = "${var.environment}-images-bucke-access-policy"
  description = "Policy for devices to access S3 backup bucket"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Effect   = "Allow"
        Resource = [
          aws_s3_bucket.capture_image_bucket.arn,
          "${aws_s3_bucket.capture_image_bucket.arn}/*",
          aws_s3_bucket.edge_logs.arn,
          "${aws_s3_bucket.edge_logs.arn}/*"

        ]
      }
    ]
  })
}


# Attach s3 policy bucket access policy to the device service user
resource "aws_iam_user_policy_attachment" "image_bucket_policy_attachment_to_user" {
  user       = var.iot_device_metrics_user_name
  policy_arn = aws_iam_policy.s3_access_to_image_bucket.arn
}

resource "aws_iam_user_policy_attachment" "image_bucket_policy_attachment_to_backend_service" {
  user       = var.platform_backend_user_name
  policy_arn = aws_iam_policy.s3_access_to_image_bucket.arn
}

