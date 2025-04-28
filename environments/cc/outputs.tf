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


output "account_id" {
    description = "Account ID"
    value = data.aws_caller_identity.current.account_id
}

output "device_certificate_policy_arn" {
    description = "ARN of the policy needed for device communication to IOT CORE"
    value = module.iot.device_policy_arn
}

output "device_certificate_policy_name" {
    description = "Name of the policy that is needed for device communication to IOT CORE"
    value = module.iot.device_policy_name
}

output "ec2_instance_ip_address" {
    description = "Dev instance IP address"
    value = module.ec2.instance_ip
}
