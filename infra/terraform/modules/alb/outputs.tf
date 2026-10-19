output "alb_arn" {
  value       = aws_lb.this.arn
  description = "ARN of the Application Load Balancer."
}

output "alb_dns_name" {
  value       = aws_lb.this.dns_name
  description = "DNS name of the ALB. Used as the HTTP_PROXY integration target in the edge (API Gateway) module."
}

output "alb_zone_id" {
  value       = aws_lb.this.zone_id
  description = "Route 53 hosted zone ID of the ALB, for alias records."
}

output "target_group_arn" {
  value       = aws_lb_target_group.this.arn
  description = "ARN of the default target group where EKS node groups register. Unused once var.routes is non-empty (per-service target groups take over routing); kept for environments/modules that don't need per-service routing."
}

output "route_target_group_arns" {
  value       = { for service, tg in aws_lb_target_group.routes : service => tg.arn }
  description = "Map of service name to its target group ARN, one entry per key in var.routes. Each value goes into a TargetGroupBinding's spec.targetGroupARN in infra/k8s/platform/, keyed the same way as var.routes."
}

output "https_listener_arn" {
  value       = local.has_certificate ? aws_lb_listener.https[0].arn : ""
  description = "ARN of the HTTPS listener, empty string when no certificate_arn was provided."
}

output "http_listener_arn" {
  value       = aws_lb_listener.http.arn
  description = "ARN of the HTTP listener."
}

output "alb_arn_suffix" {
  value       = aws_lb.this.arn_suffix
  description = "ARN suffix of the ALB (app/<name>/<id>), the form the CloudWatch metrics dimension expects."
}
