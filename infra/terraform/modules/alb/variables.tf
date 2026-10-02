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
  description = "Port the default target group forwards traffic to (EKS NodePort or pod port, depending on target_type)."
  default     = 80
}

variable "target_type" {
  type        = string
  description = "Target group target type: 'ip' (pods behind the AWS Load Balancer Controller) or 'instance' (NodePort on EKS worker nodes)."
  default     = "ip"
}

variable "health_check_path" {
  type        = string
  description = "HTTP path used by the target group health check."
  default     = "/health"
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
