# Security group for the EC2 instance
resource "aws_security_group" "app_server_sg" {
    name            =   "${var.environment}-ec2-app-server-sg"
    description     =   "Security group for the application server"

    # SSH access
    ingress {
        from_port   = 22
        to_port     = 22
        protocol    = "tcp"
        cidr_blocks = var.allowed_ssh_cidrs
        description = "SSH access"
    }

    # PostgreSQL access
    ingress {
        from_port   = 5432
        to_port     = 5432
        protocol    = "tcp"
        cidr_blocks = var.allowed_service_cidrs
        description = "PostgreSQL access"
    }

    # Frontend access (HTTP)
    ingress {
        from_port   = 3000
        to_port     = 3000
        protocol    = "tcp"
        cidr_blocks = var.allowed_service_cidrs
        description = "Frontend HTTP access"
    }

    # Backend access (HTTP)
    ingress {
        from_port   = 8000
        to_port     = 8000
        protocol    = "tcp"
        cidr_blocks = var.allowed_service_cidrs
        description = "Backend HTTP access"
    }

    # # Frontend access from ALB
    # ingress {
    #     from_port       = 3000
    #     to_port         = 3000
    #     protocol        = "tcp"
    #     security_groups = var.alb_security_group_id != "" ? [var.alb_security_group_id] : []
    #     cidr_blocks     = var.alb_security_group_id == "" ? var.allowed_service_cidrs : []
    #     description     = "Frontend HTTP access"
    # }

    # # Backend access from ALB
    # ingress {
    #     from_port       = 8000
    #     to_port         = 8000
    #     protocol        = "tcp"
    #     security_groups = var.alb_security_group_id != "" ? [var.alb_security_group_id] : []
    #     cidr_blocks     = var.alb_security_group_id == "" ? var.allowed_service_cidrs : []
    #     description     = "Backend HTTP access"
    # }


    # Allow all outboud traffic
    egress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        description = "Allow all outbound traffic"
        cidr_blocks = ["0.0.0.0/0"]
    }

    tags = {
        Name = "${var.environment}-app-server-sg"
    }
}