resource "aws_athena_workgroup" "edge_analytics" {
  name = "${var.environment}-edge-analytics-workgroup"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.bucket}/query-results/"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }

    engine_version {
      selected_engine_version = "Athena engine version 3"
    }
  }

  tags = {
    Name        = "${var.environment}-edge-analytics-workgroup"
    Environment = var.environment
  }
}

# S3 bucket for Athena query results
resource "aws_s3_bucket" "athena_results" {
  bucket = "${var.environment}-athena-query-results-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name        = "${var.environment}-athena-query-results"
    Environment = var.environment
  }
}

# S3 bucket versioning for Athena results
resource "aws_s3_bucket_versioning" "athena_results_versioning" {
  bucket = aws_s3_bucket.athena_results.id
  versioning_configuration {
    status = "Enabled"
  }
}


resource "aws_s3_bucket_lifecycle_configuration" "athena_results_lifecycle" {
  bucket = aws_s3_bucket.athena_results.id

  rule {
    id     = "cleanup-query-results"
    status = "Enabled"

    expiration {
      days = 7
    }
  }
}

# S3 bucket public access block for Athena results
resource "aws_s3_bucket_public_access_block" "athena_results_pab" {
  bucket = aws_s3_bucket.athena_results.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Glue catalog database for edge analytics
resource "aws_glue_catalog_database" "edge_analytics" {
  name = "${var.environment}_edge_analytics"

  description = "Database for edge analytics logs from Fluent Bit"
}


# Glue table for application logs with flexible context
resource "aws_glue_catalog_table" "application_logs" {
  name          = "application_logs"
  database_name = aws_glue_catalog_database.edge_analytics.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    "projection.enabled"        = "true"
    "projection.device_id.type" = "injected"

    # Year Configuration
    "projection.year.type"      = "integer"
    "projection.year.range"     = "2024,2030"
    "projection.year.digits"    = "4"

    # Month Configuration
    "projection.month.type"     = "enum"
    "projection.month.values"   = "01,02,03,04,05,06,07,08,09,10,11,12"

    # Day Configuration
    "projection.day.type"       = "enum"
    "projection.day.values"     = "01,02,03,04,05,06,07,08,09,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31"
    
    # Storage and Classification
    "storage.location.template" = "s3://${var.edge_logs_bucket_name}/logs/device_id=$${device_id}/year=$${year}/month=$${month}/day=$${day}/"
    "classification"            = "json"
    "compressionType"           = "gzip"
  }

  storage_descriptor {
    location      = "s3://${var.edge_logs_bucket_name}/logs/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      name                  = "json_serde"
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"

      parameters = {
        "serialization.format" = "1"
        "case.insensitive"     = "true"
      }
    }

    columns {
      name = "timestamp"
      type = "string"
    }
    
    columns {
      name = "level"
      type = "string"
    }
    
    columns {
      name = "component"
      type = "string"
    }
    
    columns {
      name = "message"
      type = "string"
    }
    
    # Flexible context column that accepts any key-value pairs
    columns {
      name = "context"
      type = "map<string,string>"
    }
    
    columns {
      name = "error"
      type = "string"
    }
  }

  partition_keys {
    name = "device_id"
    type = "string"
  }
  
  partition_keys {
    name = "year"
    type = "int"
  }
  
  partition_keys {
    name = "month"
    type = "string"
  }
  
  partition_keys {
    name = "day"
    type = "string"
  }
}


# Named queries for common analysis patterns
resource "aws_athena_named_query" "error_analysis" {
  name      = "${var.environment}-edge-analytics-error-analysis"
  workgroup = aws_athena_workgroup.edge_analytics.id
  database  = aws_glue_catalog_database.edge_analytics.name
  query     = <<-EOT
    SELECT 
      device_id,
      DATE_FORMAT(CAST(timestamp AS timestamp), '%Y-%m-%d %H:00:00') as hour,
      level,
      component,
      COUNT(*) as error_count,
      ARRAY_AGG(DISTINCT message) as error_messages
    FROM 
      application_logs
    WHERE 
      level IN ('ERROR', 'CRITICAL')
      AND year = YEAR(CURRENT_DATE)
      AND month = MONTH(CURRENT_DATE)
      AND day >= DAY(CURRENT_DATE) - 7
    GROUP BY 
      device_id, 
      DATE_FORMAT(CAST(timestamp AS timestamp), '%Y-%m-%d %H:00:00'),
      level,
      component
    ORDER BY 
      hour DESC, 
      error_count DESC
  EOT

  description = "Analyze errors and critical issues from the last 7 days"
}

resource "aws_athena_named_query" "device_health_check" {
  name      = "${var.environment}-edge-analytics-device-health"
  workgroup = aws_athena_workgroup.edge_analytics.id
  database  = aws_glue_catalog_database.edge_analytics.name
  query     = <<-EOT
    WITH latest_logs AS (
      SELECT 
        device_id,
        MAX(CAST(timestamp AS timestamp)) as last_seen,
        COUNT(*) as log_count
      FROM 
        application_logs
      WHERE 
        year = YEAR(CURRENT_DATE)
        AND month = MONTH(CURRENT_DATE)
        AND day >= DAY(CURRENT_DATE) - 1
      GROUP BY 
        device_id
    )
    SELECT 
      device_id,
      last_seen,
      log_count,
      CASE 
        WHEN last_seen < CURRENT_TIMESTAMP - INTERVAL '1' HOUR THEN 'OFFLINE'
        WHEN log_count < 10 THEN 'DEGRADED'
        ELSE 'HEALTHY'
      END as status
    FROM 
      latest_logs
    ORDER BY 
      status DESC, 
      last_seen DESC
  EOT

  description = "Check health status of edge devices"
}