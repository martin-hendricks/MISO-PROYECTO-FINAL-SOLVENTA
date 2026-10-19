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

variable "seed_external_provider_placeholders" {
  type        = bool
  description = <<-EOT
    When true, each external provider secret (open_finance, open_data,
    kyc_aml, pasarela_pago, firma_electronica, telemetria_iot,
    reaseguro_acord) is seeded with an obvious, non-functional placeholder
    JSON ({clientId: "PENDIENTE_<provider>", clientSecret: "PENDIENTE_<provider>"})
    instead of being left empty. Lets ms-cotizacion and other adapters
    boot in a fresh apply without a manual secretsmanager put-secret-value
    step -- useful for the minimo/pruebas environment, where nobody has the
    real third-party credentials yet.

    Set to false for any environment where getting a real credential in by
    mistake-of-omission is a real risk (shared/staging/prod): then these
    secrets are created empty, same as the DB credentials when their
    *_db_credentials var is null, and setting the real value is a deliberate
    out-of-band step every time.
  EOT
  default     = true
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into all taggable resources."
  default     = {}
}
