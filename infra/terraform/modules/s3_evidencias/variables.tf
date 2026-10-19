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
  description = "CMK ARN (kms module) used to encrypt claim evidence at rest."
}

variable "force_destroy" {
  type        = bool
  description = "Allows destroying the bucket even if it still has objects. True by default so the minimum environment stays destructible (HU-78); MUST be set to false in production, since this bucket holds sensitive customer claim evidence."
  default     = true
}

variable "bucket_suffix" {
  type        = string
  description = "Random suffix appended to the bucket name to satisfy S3's global uniqueness requirement. Leave empty to let the module generate one with random_id."
  default     = ""
}

variable "transition_ia_days" {
  type        = number
  description = "Days after object creation before transitioning to STANDARD_IA."
  default     = 90
}

variable "transition_glacier_days" {
  type        = number
  description = "Days after object creation before transitioning to GLACIER."
  default     = 365
}

variable "noncurrent_version_expiration_days" {
  type        = number
  description = "Days before non-current object versions expire and are deleted."
  default     = 730
}

variable "cors_allowed_origins" {
  type        = list(string)
  description = "Allowed origins for the bucket CORS configuration, used by the mobile app to upload claim evidence directly. Empty list disables CORS."
  default     = []
}

variable "cors_allowed_methods" {
  type        = list(string)
  description = "Allowed HTTP methods for the bucket CORS configuration."
  default     = ["GET", "PUT", "POST"]
}

variable "cors_allowed_headers" {
  type        = list(string)
  description = "Allowed request headers for the bucket CORS configuration."
  default     = ["*"]
}

variable "cors_max_age_seconds" {
  type        = number
  description = "Max age (seconds) browsers/clients may cache the CORS preflight response."
  default     = 300
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into all taggable resources."
  default     = {}
}
