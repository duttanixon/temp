# S3 bucket for storing IoT device certificates
resource "aws_s3_bucket" "certificate_bucket" {
  bucket = "${var.environment}-iot-certificates"

  tags = {
    Name        = "${var.environment}-iot-certificates"
    Description = "Bucket for storing IoT device certificates"
  }
}

# Enable versioning for the certificate bucket
resource "aws_s3_bucket_versioning" "certificate_bucket_versioning" {
  bucket = aws_s3_bucket.certificate_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Configure server-side encryption for the certificate bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "certificate_bucket_encryption" {
  bucket = aws_s3_bucket.certificate_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access to the certificate bucket
resource "aws_s3_bucket_public_access_block" "certificate_bucket_public_access" {
  bucket                  = aws_s3_bucket.certificate_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Add bucket policy to restrict access
resource "aws_s3_bucket_policy" "certificate_bucket_policy" {
  bucket = aws_s3_bucket.certificate_bucket.id

  # Only apply policy after public access block is in place
  depends_on = [aws_s3_bucket_public_access_block.certificate_bucket_public_access]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyUnencryptedObjectUploads"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.certificate_bucket.arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption" = "AES256"
          }
        }
      }
    ]
  })
}