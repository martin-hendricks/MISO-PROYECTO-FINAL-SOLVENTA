variable "project_name" {
  type        = string
  description = "Short name used in resource tags and names."
}

variable "environment" {
  type        = string
  description = "Deployment stage (e.g. minimo, experimentos)."
}

variable "log_groups" {
  type        = list(string)
  description = "Names of the CloudWatch log groups to create, one per microservice/component of the monorepo."
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

variable "log_retention_days" {
  type        = number
  description = "Retention (days) applied to every microservice log group."
  default     = 30
}

variable "kms_key_arn" {
  type        = string
  description = "CMK ARN (kms module) used to encrypt the CloudWatch log groups."
}

variable "alarm_email" {
  type        = string
  description = "Email address subscribed to the alarms SNS topic. Empty string skips the email subscription."
  default     = ""
}

variable "alb_arn_suffix" {
  type        = string
  description = "ARN suffix of the ALB (alb module output, format app/<name>/<id>), required by the ALB CloudWatch metrics dimension. Empty string skips the ALB alarms."
  default     = ""
}

variable "alb_p95_latency_threshold_seconds" {
  type        = number
  description = "p95 latency threshold (seconds) for the ALB TargetResponseTime alarm, related to EC-LAT-03."
  default     = 0.4
}

variable "alb_5xx_threshold" {
  type        = number
  description = "Number of ALB-generated 5xx responses (HTTPCode_ELB_5XX_Count) within the evaluation period that triggers the alarm."
  default     = 5
}

variable "rds_instance_ids" {
  type        = list(string)
  description = "RDS instance identifiers to monitor for high CPU (e.g. DBPolizas, DBSiniestros). Empty list skips the RDS alarms."
  default     = []
}

variable "rds_cpu_threshold_percent" {
  type        = number
  description = "CPU utilization percentage threshold for the RDS high-CPU alarm."
  default     = 80
}

variable "elasticache_cluster_ids" {
  type        = list(string)
  description = "ElastiCache Redis cluster IDs to monitor for high memory/evictions (e.g. CacheOF, CacheOD). Empty list skips the ElastiCache alarms."
  default     = []
}

variable "elasticache_memory_threshold_percent" {
  type        = number
  description = "DatabaseMemoryUsagePercentage threshold for the ElastiCache high-memory alarm."
  default     = 80
}

variable "elasticache_evictions_threshold" {
  type        = number
  description = "Evictions count within the evaluation period that triggers the ElastiCache evictions alarm."
  default     = 0
}

variable "msk_cluster_name" {
  type        = string
  description = "MSK cluster name to monitor for consumer lag and disk usage. Empty string skips the MSK alarms."
  default     = ""
}

variable "msk_consumer_lag_threshold" {
  type        = number
  description = "MaxOffsetLag threshold (records) for the MSK consumer lag alarm."
  default     = 1000
}

variable "msk_disk_usage_threshold_percent" {
  type        = number
  description = "KafkaDataLogsDiskUsed percentage threshold for the MSK disk usage alarm."
  default     = 80
}

variable "alarm_evaluation_periods" {
  type        = number
  description = "Number of consecutive evaluation periods before an alarm fires, applied to all alarms in this module."
  default     = 3
}

variable "alarm_period_seconds" {
  type        = number
  description = "Period (seconds) of each evaluation datapoint, applied to all alarms in this module."
  default     = 300
}

variable "enable_managed_prometheus" {
  type        = bool
  description = "Creates an Amazon Managed Service for Prometheus (AMP) workspace. Default false because it has a standing cost; the diagram's Prometheus/Grafana requirement is otherwise met by the in-cluster add-on."
  default     = false
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into all taggable resources."
  default     = {}
}
