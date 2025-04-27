output "backend_service_user_name" {
    description = "Name of the backend service user"
    value       = module.common.backend_service_user_name
}

output "backend_service_access_key_id" {
    description = "Name of the backend service user"
    value       = module.common.backend_service_access_key_id
}

output "backend_service_secret_access_key" {
    description = "Name of the backend service user"
    value       = module.common.backend_service_secret_access_key
    sensitive   = true
}