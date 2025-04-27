# Output the user ARN and name so other modules can reference it
output "backend_service_user_arn" {
  description = "ARN of the backend service user"
  value       = aws_iam_user.backend_service_user.arn
}

output "backend_service_user_name" {
  description = "Name of the backend service user"
  value       = aws_iam_user.backend_service_user.name
}

# Output the access key details
output "backend_service_access_key_id" {
  description = "The access key ID for the backend service user"
  value       = aws_iam_access_key.backend_service_key.id
  sensitive   = false
}

output "backend_service_secret_access_key" {
  description = "The secret access key for the backend service user"
  value       = aws_iam_access_key.backend_service_key.secret
  sensitive   = true
}