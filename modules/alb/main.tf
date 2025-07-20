# Request ACM Certificate
resource "aws_acm_certificate" "platform_cert" {
  domain_name       = var.domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "${var.environment}-platform-cert"
    Environment = var.environment
  }
}


# ALB
resource "aws_lb" "platform_alb" {
  name               = "${var.environment}-platform-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = data.aws_subnets.default.ids

  enable_deletion_protection = false
  enable_http2              = true

  tags = {
    Name        = "${var.environment}-platform-alb"
    Environment = var.environment
  }
}


# Target Group for Frontend (port 3000)
resource "aws_lb_target_group" "frontend_tg" {
  name     = "${var.environment}-frontend-tg"
  port     = 3000
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.default.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/"
    matcher             = "200"
  }

  tags = {
    Name        = "${var.environment}-frontend-tg"
    Environment = var.environment
  }
}


# Target Group for Backend API (port 8000)
resource "aws_lb_target_group" "backend_tg" {
  name     = "${var.environment}-backend-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.default.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/health" 
    matcher             = "200"
  }

  tags = {
    Name        = "${var.environment}-backend-tg"
    Environment = var.environment
  }
}


# Attach EC2 instance to Frontend Target Group
resource "aws_lb_target_group_attachment" "frontend_attachment" {
  target_group_arn = aws_lb_target_group.frontend_tg.arn
  target_id        = var.instance_id
  port             = 3000
}

# Attach EC2 instance to Backend Target Group
resource "aws_lb_target_group_attachment" "backend_attachment" {
  target_group_arn = aws_lb_target_group.backend_tg.arn
  target_id        = var.instance_id
  port             = 8000
}

# HTTP Listener (redirect to HTTPS)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.platform_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# HTTPS Listener
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.platform_alb.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate_validation.cert_validation.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend_tg.arn
  }
}

# Listener rule for API traffic
resource "aws_lb_listener_rule" "api" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend_tg.arn
  }

  condition {
    path_pattern {
      values = ["/api/v1/*"]
    }
  }
}


# Certificate Validation
resource "aws_acm_certificate_validation" "cert_validation" {
  certificate_arn         = aws_acm_certificate.platform_cert.arn
  validation_record_fqdns = [for record in aws_acm_certificate.platform_cert.domain_validation_options : record.resource_record_name]
  
  depends_on = [aws_acm_certificate.platform_cert]
}