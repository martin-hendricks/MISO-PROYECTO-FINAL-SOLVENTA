variable "project_name" {
  type        = string
  description = "Short name used in resource names and tags."
}

variable "environment" {
  type        = string
  description = "Deployment stage (e.g. minimo, dev, staging, prod)."
}

variable "github_org" {
  type        = string
  description = "GitHub organization or user that owns the repository allowed to assume this role."
}

variable "github_repo" {
  type        = string
  description = "GitHub repository name (without the org/ prefix) allowed to assume this role."
}

variable "github_branches" {
  type        = list(string)
  description = "Branches whose workflow runs may assume this role (trust policy sub condition). A push/merge on any other branch cannot authenticate as this role."
  default     = ["develop", "main"]
}

variable "github_environments" {
  type        = list(string)
  description = "GitHub Environments whose jobs may assume this role. Jobs that declare `environment:` get a sub claim of the form repo:<org>/<repo>:environment:<name> instead of the branch ref."
  default     = ["desarrollo", "produccion"]
}

variable "ecr_repository_arns" {
  type        = list(string)
  description = "ARNs of the ECR repositories (ecr module output `repository_arns`) this role may push/pull images to."
}

variable "eks_cluster_arn" {
  type        = string
  description = "ARN of the EKS cluster (eks module output `cluster_arn`) this role may describe, needed to run `aws eks update-kubeconfig`."
}

variable "eks_cluster_name" {
  type        = string
  description = "Name of the EKS cluster (eks module output `cluster_name`), needed to create the access entry that authorizes this role inside the cluster's Kubernetes API."
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into all taggable resources."
  default     = {}
}
