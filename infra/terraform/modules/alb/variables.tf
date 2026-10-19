variable "project_name" {
  type        = string
  description = "Short name used in resource tags and names."
}

variable "environment" {
  type        = string
  description = "Deployment stage (e.g. minimo, experimentos)."
}

variable "vpc_id" {
  type        = string
  description = "VPC where the ALB and its target group are created."
}

variable "subnet_ids" {
  type        = list(string)
  description = "Subnet IDs (at least two AZs) where the ALB is placed. Internal by design (EC-SEG-07): the only path in is through the API Gateway VPC Link, so this should be the private application subnets, not the public ones."
}

variable "security_group_ids" {
  type        = list(string)
  description = "Security group IDs attached to the ALB (e.g. the alb SG from the security_groups module)."
}

variable "certificate_arn" {
  type        = string
  description = "ACM certificate ARN for the HTTPS listener. Empty string when there is no domain yet (minimum environment); the HTTPS listener is then omitted and HTTP forwards directly to the target group."
  default     = ""
}

variable "ssl_policy" {
  type        = string
  description = "SSL negotiation policy for the HTTPS listener."
  default     = "ELBSecurityPolicy-TLS13-1-2-2021-06"
}

variable "target_port" {
  type        = number
  description = "Port the default target group forwards traffic to (EKS NodePort or pod port, depending on target_type). Used only when var.routes is empty."
  default     = 80
}

variable "target_type" {
  type        = string
  description = "Target group target type: 'ip' (pods behind the AWS Load Balancer Controller, registered via TargetGroupBinding) or 'instance' (NodePort on EKS worker nodes)."
  default     = "ip"
}

variable "health_check_path" {
  type        = string
  description = "HTTP path used by the default target group's health check. Each entry in var.routes can override this per service."
  default     = "/health"
}

variable "routes" {
  type = map(object({
    port              = number
    paths             = list(string)
    health_check_path = optional(string)
    priority          = number
  }))
  description = <<-EOT
    One target group + listener rule per service, keyed by service name
    (must match the Kubernetes Service name -- infra/k8s/platform/*-target-group-binding.yaml
    references these target groups by Terraform output, keyed the same way).

    Each route creates its own aws_lb_target_group (pods register into it via
    a TargetGroupBindin, not via Kubernetes Ingress -- this module's ALB is
    the single internal ALB the API Gateway VPC Link points to; an Ingress
    would create a SEPARATE AWS Load Balancer Controller-managed ALB,
    disconnected from this one and from the API Gateway) and one or more
    aws_lb_listener_rule entries (one per path) on the HTTP listener,
    forwarding by path prefix.

    priority is the BASE rule priority for this service; a service with N
    paths consumes priority, priority+1, ..., priority+(N-1) (one
    aws_lb_listener_rule per path). Space entries at least 10 apart (e.g.
    10, 20, 30) so a service can gain more paths later without colliding
    with the next one's range. ALB listener rule priorities are global to
    the listener (not per target group) and must all be unique; lower is
    evaluated first.

    Empty map (default) falls back to the single default target group
    (aws_lb_target_group.this) with no listener rules -- the pre-routes
    behavior, kept for modules/environments that don't need per-service
    routing.
  EOT
  default     = {}
}

variable "enable_deletion_protection" {
  type        = bool
  description = "Protects the ALB from accidental deletion. False by default so the environment stays destructible (HU-78)."
  default     = false
}

variable "access_logs_bucket" {
  type        = string
  description = "S3 bucket name for ALB access logs. Empty string disables access logging."
  default     = ""
}

variable "access_logs_prefix" {
  type        = string
  description = "Key prefix inside access_logs_bucket for ALB access logs."
  default     = "alb"
}

variable "idle_timeout" {
  type        = number
  description = "Idle timeout (seconds) for connections through the ALB."
  default     = 60
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into all taggable resources."
  default     = {}
}
