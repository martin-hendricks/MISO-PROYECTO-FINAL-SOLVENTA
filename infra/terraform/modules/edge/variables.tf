variable "project_name" {
  type        = string
  description = "Short name used in resource tags and names."
}

variable "environment" {
  type        = string
  description = "Deployment stage (e.g. minimo, experimentos)."
}

variable "kms_key_arn" {
  type        = string
  description = "CMK ARN (kms module) used to encrypt the SPA S3 bucket and the API Gateway access log group."
}

variable "alb_listener_arn" {
  type        = string
  description = "ARN of the internal ALB's listener (alb module output). This is what a VPC_LINK integration targets -- not the ALB's DNS name, which only an internet-reachable HTTP_PROXY integration would use (EC-SEG-07: the ALB here has no public path)."
}

variable "vpc_link_subnet_ids" {
  type        = list(string)
  description = "Subnet IDs (at least two AZs) where the API Gateway VPC Link's ENIs are placed. Must be able to route to the ALB's subnets -- the private application subnets."
}

variable "vpc_link_security_group_ids" {
  type        = list(string)
  description = "Security group IDs attached to the VPC Link's ENIs (the vpc_link SG from the security_groups module, which is the only principal the ALB's security group allows in)."
}

variable "spa_bucket_force_destroy" {
  type        = bool
  description = "Allows destroying the SPA bucket even if it still has objects. True by default so the environment stays destructible (HU-78)."
  default     = true
}

variable "bucket_suffix" {
  type        = string
  description = "Random suffix appended to the SPA bucket name to satisfy S3's global uniqueness requirement. Leave empty to let the module generate one with random_id."
  default     = ""
}

variable "cloudfront_price_class" {
  type        = string
  description = "CloudFront price class, controls edge location coverage vs. cost."
  default     = "PriceClass_100"
}

variable "waf_rate_limit" {
  type        = number
  description = "Maximum requests per 5-minute window, per client IP, before the WAF rate-based rule blocks it."
  default     = 2000
}

variable "waf_managed_rules_action" {
  type        = string
  description = "Action for the AWS managed rule groups: 'count' (observe only) or 'block' (enforce)."
  default     = "block"

  validation {
    condition     = contains(["count", "block"], var.waf_managed_rules_action)
    error_message = "waf_managed_rules_action must be 'count' or 'block'."
  }
}

variable "apigw_throttling_burst_limit" {
  type        = number
  description = "API Gateway default route throttling burst limit. Matters because the diagram shows the API Gateway as the entry point for distribution partners (socios)."
  default     = 100
}

variable "apigw_throttling_rate_limit" {
  type        = number
  description = "API Gateway default route throttling steady-state rate limit (requests/second)."
  default     = 50
}

variable "apigw_log_retention_days" {
  type        = number
  description = "Retention (days) for the API Gateway access log CloudWatch log group."
  default     = 30
}

variable "cors_allow_origins" {
  type        = list(string)
  description = "Allowed origins for the API Gateway CORS configuration."
  default     = ["*"]
}

variable "cors_allow_methods" {
  type        = list(string)
  description = "Allowed HTTP methods for the API Gateway CORS configuration."
  default     = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
}

variable "cors_allow_headers" {
  type        = list(string)
  description = "Allowed request headers for the API Gateway CORS configuration."
  default     = ["Content-Type", "Authorization"]
}

variable "cors_max_age" {
  type        = number
  description = "Max age (seconds) browsers may cache the API Gateway CORS preflight response."
  default     = 300
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into all taggable resources."
  default     = {}
}
