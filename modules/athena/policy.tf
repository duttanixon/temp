# IAM user for Superset to access Athena and S3
resource "aws_iam_user" "superset_athena_user" {
  name = "${var.environment}-superset-athena-user"

  tags = {
    Name        = "${var.environment}-superset-athena-user"
    Environment = var.environment
    Purpose     = "Superset access to Athena and S3"
  }
}

# Create access key for Superset user
resource "aws_iam_access_key" "superset_athena_access_key" {
  user = aws_iam_user.superset_athena_user.name
}



# IAM role for Superset to assume (for better security)
resource "aws_iam_role" "superset_athena_role" {
  name = "${var.environment}-superset-athena-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_user.superset_athena_user.arn
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "${var.environment}-superset-athena-role"
    Environment = var.environment
  }
}




# IAM policy for Superset to access Athena and S3
resource "aws_iam_policy" "superset_athena_policy" {
  name = "${var.environment}-superset-athena-policy"
  description = "Policy for Superset to access Athena and S3"

  policy = jsonencode({
    Version = "2012-10-17"
  Statement = [
    {
      Effect = "Allow"
      Action = [
        "athena:BatchGetQueryExecution",
        "athena:GetQueryExecution",
        "athena:GetQueryResults",
        "athena:StartQueryExecution",
        "athena:StopQueryExecution",
        "athena:ListWorkGroups",
        "athena:GetWorkGroup",
        "athena:ListDataCatalogs",
        "athena:GetDataCatalog",
        "athena:ListDatabases",
        "athena:GetDatabase",
        "athena:ListTableMetadata",
        "athena:GetTableMetadata",
        "athena:ListQueryExecutions",
        "athena:GetQueryResultsStream"
      ]
      Resource = [
        # aws_athena_workgroup.edge_analytics.arn,
        # "arn:aws:athena:${var.aws_region}:${data.aws_caller_identity.current.account_id}:datacatalog/AwsDataCatalog"
        "*"
      ]
    },
    {
      Effect = "Allow"
      Action = [
        "glue:GetDatabase",
        "glue:GetDatabases",
        "glue:GetTable",
        "glue:GetTables",
        "glue:GetPartition",
        "glue:GetPartitions",
        "glue:BatchGetPartition"
      ]
      Resource = [
        "*"
        # aws_glue_catalog_database.edge_analytics.arn,
        # "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:catalog",
        # "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:database/${aws_glue_catalog_database.edge_analytics.name}",
        # "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/${aws_glue_catalog_database.edge_analytics.name}/*"
      ]
    },
    {
      Effect = "Allow"
      Action = [
        "s3:GetBucketLocation",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:ListBucketMultipartUploads",
        "s3:ListMultipartUploadParts",
        "s3:AbortMultipartUpload",
        "s3:PutObject",
        "s3:PutObjectAcl"
      ]
      Resource = [
        "arn:aws:s3:::${var.edge_logs_bucket_name}",
        "arn:aws:s3:::${var.edge_logs_bucket_name}/*",
        aws_s3_bucket.athena_results.arn,
        "${aws_s3_bucket.athena_results.arn}/*"
      ]
    },
    {
      Effect = "Allow"
      Action = [
        "s3:ListAllMyBuckets"
        ]
      Resource = "*"
    }
    ]
  })
  }


# Attach policy to user
resource "aws_iam_user_policy_attachment" "superset_athena_user_policy_attachment" {
  user       = aws_iam_user.superset_athena_user.name
  policy_arn = aws_iam_policy.superset_athena_policy.arn
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "superset_athena_role_policy_attachment" {
  role       = aws_iam_role.superset_athena_role.name
  policy_arn = aws_iam_policy.superset_athena_policy.arn
}

# Policy to allow user to assume the role
resource "aws_iam_policy" "superset_assume_role_policy" {
  name        = "${var.environment}-superset-assume-role-policy"
  description = "Policy to allow Superset user to assume the Athena role"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "sts:AssumeRole"
        Resource = aws_iam_role.superset_athena_role.arn
      }
    ]
  })
}

# Attach assume role policy to user
resource "aws_iam_user_policy_attachment" "superset_assume_role_attachment" {
  user       = aws_iam_user.superset_athena_user.name
  policy_arn = aws_iam_policy.superset_assume_role_policy.arn
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}