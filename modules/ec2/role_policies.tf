# IAM role for EC2 instance
resource "aws_iam_role" "ec2_role" {
  name = "${var.environment}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for S3 access
resource "aws_iam_policy" "s3_access" {
  name        = "${var.environment}-s3-access-policy"
  description = "Policy for EC2 to access S3 backup bucket"

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
          aws_s3_bucket.app_backups.arn,
          "${aws_s3_bucket.app_backups.arn}/*"
        ]
      }
    ]
  })
}

# Attach S3 policy to EC2 role
resource "aws_iam_role_policy_attachment" "s3_attach_policy_to_ec2_role" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.s3_access.arn
}

# Instance profile for EC2
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.environment}-ec2-profile"
  role = aws_iam_role.ec2_role.name
}
