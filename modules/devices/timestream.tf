resource "aws_timestreamwrite_database" "metrics_db" {
  database_name = "${var.environment}-${var.edge_device_metrics_database_name}"
  tags = {
    Name        = "${var.environment}-${var.edge_device_metrics_database_name}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_timestreamwrite_table" "raw_metrics" {
  database_name = aws_timestreamwrite_database.metrics_db.database_name
  table_name    = "${var.environment}_${var.raw_table_name}"
  
  retention_properties {
    memory_store_retention_period_in_hours = var.raw_memory_retention_hours
    magnetic_store_retention_period_in_days = var.raw_magnetic_retention_days
  }

  tags = {
    Name        = "${var.environment}_${var.raw_table_name}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_timestreamwrite_table" "hourly_metrics" {
  database_name = aws_timestreamwrite_database.metrics_db.database_name
  table_name    = "${var.environment}_${var.hourly_table_name}"
  
  retention_properties {
    memory_store_retention_period_in_hours = var.hourly_memory_retention_hours
    magnetic_store_retention_period_in_days = var.hourly_magnetic_retention_days
  }

  tags = {
    Name        = "${var.environment}_${var.hourly_table_name}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}


resource "aws_timestreamwrite_table" "daily_metrics" {
  database_name = aws_timestreamwrite_database.metrics_db.database_name
  table_name    = "${var.environment}_${var.daily_table_name}"
  
  retention_properties {
    memory_store_retention_period_in_hours = var.daily_memory_retention_hours
    magnetic_store_retention_period_in_days = var.daily_magnetic_retention_days
  }

  tags = {
    Name        = "${var.environment}_${var.daily_table_name}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}