variable "project_name" {
  type        = string
  description = "Short name used in resource tags and names."
}

variable "environment" {
  type        = string
  description = "Deployment stage (e.g. minimo, dev, staging, prod)."
}

variable "cluster_name" {
  type        = string
  description = "Name of the EKS cluster (output of the eks module) where the add-ons are installed."
}

variable "oidc_provider_arn" {
  type        = string
  description = "ARN of the cluster's IAM OIDC provider (output of the eks module), used to build IRSA trust policies."
}

variable "oidc_provider_url" {
  type        = string
  description = "OIDC issuer URL without the https:// prefix (output of the eks module), used in IRSA trust policy conditions."
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where the cluster runs (required by the AWS Load Balancer Controller)."
}

variable "aws_region" {
  type        = string
  description = "AWS region of the cluster, passed to Helm charts that need it (e.g. Cluster Autoscaler)."
}

# --- AWS Load Balancer Controller ---

variable "enable_aws_load_balancer_controller" {
  type        = bool
  description = "Whether to install the AWS Load Balancer Controller."
  default     = true
}

variable "aws_load_balancer_controller_chart_version" {
  type        = string
  description = "Helm chart version for aws-load-balancer-controller."
  default     = "1.8.1"
}

# --- Cluster Autoscaler ---

variable "enable_cluster_autoscaler" {
  type        = bool
  description = "Whether to install the Cluster Autoscaler."
  default     = true
}

variable "cluster_autoscaler_chart_version" {
  type        = string
  description = "Helm chart version for cluster-autoscaler."
  default     = "9.37.0"
}

# --- External Secrets Operator ---

variable "enable_external_secrets" {
  type        = bool
  description = "Whether to install the External Secrets Operator."
  default     = true
}

variable "external_secrets_chart_version" {
  type        = string
  description = "Helm chart version for external-secrets."
  default     = "0.9.20"
}

# --- Metrics Server ---

variable "enable_metrics_server" {
  type        = bool
  description = "Whether to install the Metrics Server."
  default     = true
}

variable "metrics_server_chart_version" {
  type        = string
  description = "Helm chart version for metrics-server."
  default     = "3.12.1"
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into all taggable resources (IAM roles/policies)."
  default     = {}
}
