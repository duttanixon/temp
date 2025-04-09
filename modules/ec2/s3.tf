# S3 bucket for backups and storage
resource "aws_s3_bucket" "app_backups" {
    bucket = "${var.environment}-app-backups"

    tags = {
        Name = "${var.environment}-app-backups"
    }
}

resource "aws_s3_bucket_versioning" "app_backups_versioning" {
    bucket  =  aws_s3_bucket.app_backups.id

    versioning_configuration {
        status = "Enabled"
    }
}

resource "aws_s3_bucket_lifecycle_configuration" "app_backups_lifecycle" {
    bucket = aws_s3_bucket.app_backups.id

    rule {
        id      = "cleanup-old-backups"
        status  =  "Enabled"

        filter {
        prefix = "" # Apply to all objects
        }
        expiration {
            days = 90
        }
    }
}