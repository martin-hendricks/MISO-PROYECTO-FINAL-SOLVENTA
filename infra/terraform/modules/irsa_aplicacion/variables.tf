variable "project_name" {
  type        = string
  description = "Short name used in resource names and tags."
}

variable "environment" {
  type        = string
  description = "Deployment stage (e.g. minimo, experimentos)."
}

variable "namespace" {
  type        = string
  description = "Kubernetes namespace the workloads run in. It is part of the trust policy condition, so it must match the namespace in infra/k8s/platform/namespace.yaml."
  default     = "solventa"
}

variable "oidc_provider_arn" {
  type        = string
  description = "ARN of the cluster OIDC provider (eks module output). Federated principal of every trust policy here."
}

variable "oidc_provider_url" {
  type        = string
  description = "Issuer URL of the cluster OIDC provider without the https:// scheme (eks module output), used to build the sub and aud conditions."
}

variable "evidencias_bucket_arn" {
  type        = string
  description = "ARN of the claim evidence bucket (s3_evidencias module output)."
}

variable "s3_kms_key_arn" {
  type        = string
  description = "ARN of the CMK encrypting the evidence bucket. Without kms:GenerateDataKey the uploads fail even when the S3 permissions are correct."
}

variable "msk_cluster_arn" {
  type        = string
  description = "ARN of the MSK cluster (msk module output). Topic and consumer group ARNs are derived from it."
}

variable "msk_kms_key_arn" {
  type        = string
  description = "ARN of the CMK encrypting MSK data at rest."
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into all taggable resources."
  default     = {}
}
