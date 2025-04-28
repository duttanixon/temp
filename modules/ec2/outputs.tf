output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.app_server.id
}

output "instance_ip" {
  description = "IP of the EC2 instance"
  value = aws_eip.app_server_eip.public_ip
}
