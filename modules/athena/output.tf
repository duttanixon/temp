# modules/athena/outputs.tf

output "athena_workgroup_name" {
  description = "Name of the Athena workgroup"
  value       = aws_athena_workgroup.edge_analytics.name
}

output "athena_workgroup_arn" {
  description = "ARN of the Athena workgroup"
  value       = aws_athena_workgroup.edge_analytics.arn
}

output "athena_results_bucket_name" {
  description = "Name of the S3 bucket for Athena query results"
  value       = aws_s3_bucket.athena_results.bucket
}

output "glue_database_name" {
  description = "Name of the Glue catalog database"
  value       = aws_glue_catalog_database.edge_analytics.name
}

output "quicksight_athena_role_arn" {
  description = "ARN of the IAM role for QuickSight to access Athena"
  value       = aws_iam_role.quicksight_athena_role.arn
}

output "application_logs_table_name" {
  description = "Name of the application logs Glue table"
  value       = aws_glue_catalog_table.application_logs.name
}


output "athena_queries" {
  description = "Named Athena queries for common analysis patterns"
  value = {
    error_analysis     = aws_athena_named_query.error_analysis.name
    performance_metrics = aws_athena_named_query.performance_metrics.name
    device_health_check = aws_athena_named_query.device_health_check.name
  }
}