variable "project_name" {
  type        = string
  description = "Short name used in resource tags and names."
}

variable "environment" {
  type        = string
  description = "Deployment stage (e.g. minimo, experimentos)."
}

variable "private_data_subnet_ids" {
  type        = list(string)
  description = "Private data subnets (one per AZ) used for the DB subnet group. Multi-AZ requires at least two AZs here."
}

variable "vpc_security_group_ids" {
  type        = list(string)
  description = "Security group ids for RDS (typically the RDS tier SG from the security_groups module)."
}

variable "db_name" {
  type        = string
  description = "Initial database name for DBSiniestros."
  default     = "siniestros"
}

variable "db_username" {
  type        = string
  description = "Master username."
  default     = "siniestros_admin"
}

variable "engine_version" {
  type        = string
  description = "PostgreSQL engine version."
  default     = "16.4"
}

variable "instance_class" {
  type        = string
  description = "Instance class for the DB instance."
  default     = "db.t4g.medium"
}

variable "allocated_storage" {
  type        = number
  description = "Allocated storage in GB."
  default     = 20
}

variable "max_allocated_storage" {
  type        = number
  description = "Storage autoscaling upper bound in GB; set equal to allocated_storage to disable autoscaling."
  default     = 100
}

variable "backup_retention_period" {
  type        = number
  description = "Automated backup retention in days. Kept high by default because RPO matters for the claims ledger (EC-DISP-06/07)."
  default     = 7
}

variable "skip_final_snapshot" {
  type        = bool
  description = "Skip final snapshot on destroy. True by default: this is a destructible environment (HU-78) and terraform destroy must leave the account clean."
  default     = true
}

variable "deletion_protection" {
  type        = bool
  description = "Enable RDS deletion protection. False by default for the destructible minimum environment (HU-78)."
  default     = false
}

variable "performance_insights_enabled" {
  type        = bool
  description = "Enable Performance Insights on the instance."
  default     = true
}

variable "kms_key_id" {
  type        = string
  description = "ARN of the CMK used to encrypt storage and Performance Insights data."
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into all taggable resources."
  default     = {}
}
