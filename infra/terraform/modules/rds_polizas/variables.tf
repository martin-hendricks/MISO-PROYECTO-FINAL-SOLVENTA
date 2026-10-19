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
  description = "Private data subnets (one per AZ) used for the DB subnet group. The primary and its read replica must land in different AZs from this list."
}

variable "vpc_security_group_ids" {
  type        = list(string)
  description = "Security group ids for RDS (typically the RDS tier SG from the security_groups module)."
}

variable "db_name" {
  type        = string
  description = "Initial database name for DBPolizas."
  default     = "polizas"
}

variable "db_username" {
  type        = string
  description = "Master username for the primary instance."
  default     = "polizas_admin"
}

variable "engine_version" {
  type        = string
  description = "PostgreSQL engine version."
  default     = "16.4"
}

variable "instance_class" {
  type        = string
  description = "Instance class for the primary DB instance."
  default     = "db.t4g.medium"
}

variable "replica_instance_class" {
  type        = string
  description = "Instance class for the read replica. Defaults to the same class as the primary; override to right-size the replica independently since it absorbs the read-heavy traffic (EC-LAT-10)."
  default     = "db.t4g.medium"
}

variable "allocated_storage" {
  type        = number
  description = "Allocated storage in GB for the primary instance."
  default     = 20
}

variable "max_allocated_storage" {
  type        = number
  description = "Storage autoscaling upper bound in GB; set equal to allocated_storage to disable autoscaling."
  default     = 100
}

variable "multi_az" {
  type        = bool
  description = "Enable Multi-AZ standby for the primary instance, independent of the active read replica described below."
  default     = true
}

variable "create_read_replica" {
  type        = bool
  description = "Whether to create the active read replica that serves production read traffic (EC-LAT-10). Set to false only for throwaway/experiment environments that don't need to validate the read-scaling path."
  default     = true
}

variable "backup_retention_period" {
  type        = number
  description = "Automated backup retention in days for the primary instance."
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
  description = "Enable Performance Insights on both primary and replica to evidence the p95 <= 150 ms latency budget of EC-LAT-10."
  default     = true
}

variable "kms_key_id" {
  type        = string
  description = "ARN of the CMK used to encrypt storage and Performance Insights data for the primary and the replica."
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into all taggable resources."
  default     = {}
}
