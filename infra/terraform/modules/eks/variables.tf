variable "project_name" {
  type        = string
  description = "Short name used in resource tags and names."
}

variable "environment" {
  type        = string
  description = "Deployment stage (e.g. minimo, dev, staging, prod)."
}

variable "kubernetes_version" {
  type        = string
  description = "EKS control plane Kubernetes version."
  default     = "1.31"
}

variable "vpc_id" {
  type        = string
  description = "VPC where the cluster and node groups are created."
}

variable "private_app_subnet_ids" {
  type        = list(string)
  description = "Private application subnet IDs (multi-AZ) where the control plane ENIs and both node groups are placed."
}

variable "kms_key_arn" {
  type        = string
  description = "ARN of the CMK (from the kms module) used to encrypt Kubernetes secrets (envelope encryption)."
}

variable "node_security_group_ids" {
  type        = list(string)
  description = "Additional security group IDs attached to the worker nodes (e.g. the EKS nodes SG from security_groups)."
  default     = []
}

variable "endpoint_public_access" {
  type        = bool
  description = "Whether the EKS public API endpoint is enabled. The private endpoint is always enabled."
  default     = true
}

variable "public_access_cidrs" {
  type        = list(string)
  description = "CIDR blocks allowed to reach the public API endpoint when endpoint_public_access is true."
  default     = ["0.0.0.0/0"]
}

# --- Grupo A: ms-cotizacion (MotorRating) + ms-perfilamiento (MotorRiesgo) ---
# Curvas de carga independientes, escalamiento vertical, warm pool, capacidad
# ampliada <= 60 s (EC-ESC-02). Cómputo intensivo, aislado del resto por taint.

variable "node_group_a_instance_types" {
  type        = list(string)
  description = "Instance types for grupo-a (ms-cotizacion / ms-perfilamiento), compute-intensive workloads."
  default     = ["c6i.xlarge"]
}

variable "node_group_a_capacity_type" {
  type        = string
  description = "Capacity type for grupo-a nodes (ON_DEMAND or SPOT). ON_DEMAND keeps the warm pool predictable for EC-ESC-02."
  default     = "ON_DEMAND"
}

variable "node_group_a_min_size" {
  type        = number
  description = "Minimum node count for grupo-a."
  default     = 2
}

variable "node_group_a_desired_size" {
  type        = number
  description = "Desired node count for grupo-a."
  default     = 2
}

variable "node_group_a_max_size" {
  type        = number
  description = "Maximum node count for grupo-a (vertical/horizontal scale-out ceiling)."
  default     = 6
}

variable "node_group_a_disk_size" {
  type        = number
  description = "Root EBS volume size (GiB) for grupo-a nodes."
  default     = 50
}

variable "node_group_a_taint_enabled" {
  type        = bool
  description = "If true, applies a NoSchedule taint (solventa.io/scaling-group=a) so only ms-cotizacion and ms-perfilamiento (with matching toleration) are scheduled on grupo-a."
  default     = true
}

# --- Grupo B: resto de microservicios, BFFs y adaptadores ---

variable "node_group_b_instance_types" {
  type        = list(string)
  description = "Instance types for grupo-b (general-purpose microservices, BFFs, adapters)."
  default     = ["m6i.large"]
}

variable "node_group_b_capacity_type" {
  type        = string
  description = "Capacity type for grupo-b nodes (ON_DEMAND or SPOT)."
  default     = "ON_DEMAND"
}

variable "node_group_b_min_size" {
  type        = number
  description = "Minimum node count for grupo-b."
  default     = 2
}

variable "node_group_b_desired_size" {
  type        = number
  description = "Desired node count for grupo-b."
  default     = 3
}

variable "node_group_b_max_size" {
  type        = number
  description = "Maximum node count for grupo-b."
  default     = 8
}

variable "node_group_b_disk_size" {
  type        = number
  description = "Root EBS volume size (GiB) for grupo-b nodes."
  default     = 30
}

variable "addon_versions" {
  type        = map(string)
  description = "Optional explicit versions for managed add-ons (vpc-cni, coredns, kube-proxy, aws-ebs-csi-driver). Keys not present default to the most recent version supported by the cluster."
  default     = {}
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into all taggable resources."
  default     = {}
}
