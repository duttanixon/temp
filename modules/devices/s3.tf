resource "aws_s3_bucket" "capture_image_bucket" {
    bucket = "${var.environment}-captured-images"

    tags = {
        Name = "${var.environment}-capture-images"
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
          "${aws_s3_bucket.capture_image_bucket.arn}/*"
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

