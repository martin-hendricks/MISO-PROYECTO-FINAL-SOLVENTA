variable "project_name" {
  type        = string
  description = "Short name used in resource tags and names."
}

variable "environment" {
  type        = string
  description = "Deployment stage (e.g. minimo, experimentos)."
}

variable "kms_key_id" {
  type        = string
  description = "KMS key ARN or ID used to encrypt all secrets (the 'secrets' CMK from the kms module)."
}

variable "recovery_window_in_days" {
  type        = number
  description = "Recovery window (in days) before a deleted secret is purged. 0 disables recovery entirely, so the environment stays destructible (HU-78)."
  default     = 0
}

variable "polizas_db_credentials" {
  type = object({
    username = string
    password = string
    host     = optional(string)
    port     = optional(number)
    dbname   = optional(string)
  })
  description = "Optional initial credentials for DBPolizas. When null, the secret is created empty (no version) and the value is set out-of-band."
  default     = null
  sensitive   = true
}

variable "siniestros_db_credentials" {
  type = object({
    username = string
    password = string
    host     = optional(string)
    port     = optional(number)
    dbname   = optional(string)
  })
  description = "Optional initial credentials for DBSiniestros. When null, the secret is created empty (no version) and the value is set out-of-band."
  default     = null
  sensitive   = true
}

variable "compartida_db_credentials" {
  type = object({
    username = string
    password = string
    host     = optional(string)
    port     = optional(number)
    dbname   = optional(string)
  })
  description = "Optional initial master credentials for DBCompartida. When null, the secret is created empty (no version) and the value is set out-of-band."
  default     = null
  sensitive   = true
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into all taggable resources."
  default     = {}
}
