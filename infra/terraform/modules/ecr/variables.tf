variable "project_name" {
  type        = string
  description = "Short name used in resource tags and names."
}

variable "environment" {
  type        = string
  description = "Deployment stage (e.g. minimo, dev, staging, prod)."
}

variable "repositories" {
  type        = list(string)
  description = "Deployable component names, one ECR repository per entry. Defaults to the 12 monorepo microservices plus the analitica and notificaciones components shown as deployable in the deployment diagram."
  default = [
    "ms-cotizacion",
    "ms-suscripcion",
    "ms-polizas",
    "ms-siniestros",
    "ms-parametrico",
    "ms-perfilamiento",
    "ms-consentimiento",
    "ms-identidad",
    "ms-pagos",
    "bff-web",
    "bff-movil",
    "api-socios",
    "analitica",
    "notificaciones",
  ]
}

variable "kms_key_arn" {
  type        = string
  description = "ARN of the CMK (from the kms module) used to encrypt repository images at rest."
}

variable "image_tag_mutability" {
  type        = string
  description = "Whether image tags can be overwritten (MUTABLE) or not (IMMUTABLE)."
  default     = "MUTABLE"
}

variable "force_delete" {
  type        = bool
  description = "If true, repositories can be deleted even if they still contain images. Kept true by default so the minimal environment stays destructible (HU-78)."
  default     = true
}

variable "max_image_count" {
  type        = number
  description = "Number of most recent tagged images to retain per repository before the lifecycle policy expires older ones."
  default     = 10
}

variable "untagged_expiry_days" {
  type        = number
  description = "Number of days after which untagged images are expired by the lifecycle policy."
  default     = 7
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into all taggable resources."
  default     = {}
}
