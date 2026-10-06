variable "project_name" {
  type        = string
  description = "Short name used in resource tags and names."
}

variable "environment" {
  type        = string
  description = "Deployment stage (e.g. minimo, experimentos)."
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC."
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  type        = list(string)
  description = "AZ names to use (at least two, for Multi-AZ activo-activo EC-DISP-06)."

  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "availability_zones must contain at least 2 AZs."
  }
}

variable "single_nat_gateway" {
  type        = bool
  description = "If true, one NAT gateway shared by all private subnets (lower cost, single point of failure). If false, one NAT gateway per AZ."
  default     = true
}

variable "cluster_name" {
  type        = string
  description = "EKS cluster name. When set (non-empty), tags public and private-app subnets with kubernetes.io/cluster/<name> = shared so the ALB Controller and cluster autoscaler can discover them."
  default     = ""
}

variable "enable_flow_logs" {
  type        = bool
  description = "If true, enables VPC Flow Logs shipped to a CloudWatch Logs group."
  default     = true
}

variable "flow_logs_retention_in_days" {
  type        = number
  description = "Retention (in days) for the VPC Flow Logs CloudWatch log group."
  default     = 30
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into all taggable resources."
  default     = {}
}
