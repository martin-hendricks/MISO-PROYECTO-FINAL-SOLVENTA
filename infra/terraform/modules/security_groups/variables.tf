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
  description = "VPC ID where the security groups are created."
}

variable "vpc_cidr" {
  type        = string
  description = "VPC IPv4 CIDR block, used for intra-VPC egress/ingress rules."
}

variable "node_port_range_start" {
  type        = number
  description = "Lower bound of the Kubernetes NodePort range used by the ALB to reach EKS nodes."
  default     = 30000
}

variable "node_port_range_end" {
  type        = number
  description = "Upper bound of the Kubernetes NodePort range used by the ALB to reach EKS nodes."
  default     = 32767
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into all taggable resources."
  default     = {}
}
