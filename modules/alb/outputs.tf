output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.platform_alb.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = aws_lb.platform_alb.zone_id
}

output "acm_certificate_arn" {
  description = "ARN of the ACM certificate"
  value       = aws_acm_certificate.platform_cert.arn
}

output "acm_certificate_validation_records" {
  description = "DNS validation records for ACM certificate"
  value = [
    for dvo in aws_acm_certificate.platform_cert.domain_validation_options : {
      name   = dvo.resource_record_name
      type   = dvo.resource_record_type
      value  = dvo.resource_record_value
    }
  ]
}

output "frontend_target_group_arn" {
  description = "ARN of the frontend target group"
  value       = aws_lb_target_group.frontend_tg.arn
}

output "backend_target_group_arn" {
  description = "ARN of the backend target group"
  value       = aws_lb_target_group.backend_tg.arn
}

output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = aws_security_group.alb_sg.id
}