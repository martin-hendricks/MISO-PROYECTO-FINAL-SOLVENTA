locals {
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags
  )

  has_certificate = length(var.certificate_arn) > 0
  has_access_logs = length(var.access_logs_bucket) > 0
}

# --- Application Load Balancer, internal (EC-SEG-07) ---
# Receives traffic ONLY from the API Gateway VPC Link (edge module) and
# balances it towards the EKS node groups in AZ-a and AZ-b (eks module). It is
# internal and has no public IP: before this, the ALB had a public-facing
# listener open to 0.0.0.0/0, which let anyone call it directly and skip the
# API Gateway's WAF and throttling entirely.

resource "aws_lb" "this" {
  name               = "${var.project_name}-${var.environment}-alb"
  internal           = true
  load_balancer_type = "application"
  security_groups    = var.security_group_ids
  subnets            = var.subnet_ids

  idle_timeout                     = var.idle_timeout
  enable_deletion_protection       = var.enable_deletion_protection
  drop_invalid_header_fields       = true
  enable_cross_zone_load_balancing = true

  dynamic "access_logs" {
    for_each = local.has_access_logs ? [1] : []
    content {
      bucket  = var.access_logs_bucket
      prefix  = var.access_logs_prefix
      enabled = true
    }
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-alb" })
}

# --- Default target group ---
# EKS node groups (AZ-a, AZ-b) register here, either as pod IPs (target_type
# = "ip", via the AWS Load Balancer Controller) or as NodePort instances.

resource "aws_lb_target_group" "this" {
  name        = "${var.project_name}-${var.environment}-tg"
  port        = var.target_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = var.target_type

  health_check {
    enabled             = true
    path                = var.health_check_path
    protocol            = "HTTP"
    matcher             = "200-399"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 3
    unhealthy_threshold = 3
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-tg" })
}

# --- HTTP listener (port 80) ---
# Redirects to HTTPS when a certificate is configured; otherwise forwards
# directly to the target group (minimum environment, no domain yet).

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  dynamic "default_action" {
    for_each = local.has_certificate ? [1] : []
    content {
      type = "redirect"
      redirect {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  }

  dynamic "default_action" {
    for_each = local.has_certificate ? [] : [1]
    content {
      type             = "forward"
      target_group_arn = aws_lb_target_group.this.arn
    }
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-http-listener" })
}

# --- HTTPS listener (port 443), only created once a certificate exists ---

resource "aws_lb_listener" "https" {
  count = local.has_certificate ? 1 : 0

  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = var.ssl_policy
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-https-listener" })
}

# --- Per-service target groups and listener rules (var.routes) ---
#
# One target group per service, so each can be health-checked and scaled
# independently. Pods register here via a Kubernetes TargetGroupBinding
# (infra/k8s/platform/), not via Ingress: an Ingress with the AWS Load
# Balancer Controller creates its OWN separate ALB, which the API Gateway
# VPC Link (module `edge`) would never route to -- confirmed in practice,
# the Ingress approach left two disconnected ALBs, one empty (this one,
# where the API Gateway points) and one with real routes (the one the
# controller created from the Ingress, which the API Gateway never saw).

resource "aws_lb_target_group" "routes" {
  for_each = var.routes

  name        = "${var.project_name}-${var.environment}-${each.key}-tg"
  port        = each.value.port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = var.target_type

  health_check {
    enabled             = true
    path                = coalesce(each.value.health_check_path, var.health_check_path)
    protocol            = "HTTP"
    matcher             = "200-399"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 3
    unhealthy_threshold = 3
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-${each.key}-tg" })
}

locals {
  # One listener_rule entry per (service, path) pair, flattened out of
  # var.routes -- a service with N paths needs N listener rules, each
  # forwarding to the same per-service target group. priority is per PATH,
  # not per service (route.priority + an offset for the path's index in the
  # list): a service with 2 paths needs 2 distinct rule priorities, or AWS
  # rejects the second aws_lb_listener_rule with a duplicate-priority error.
  route_rules = merge([
    for service, route in var.routes : {
      for idx, path in route.paths : "${service}-${replace(path, "/", "-")}" => {
        service  = service
        path     = path
        priority = route.priority + idx
      }
    }
  ]...)
}

resource "aws_lb_listener_rule" "routes" {
  for_each = local.route_rules

  listener_arn = aws_lb_listener.http.arn
  priority     = each.value.priority

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.routes[each.value.service].arn
  }

  condition {
    path_pattern {
      values = ["${each.value.path}*"]
    }
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-${each.key}-rule" })
}
