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
  description = "Private data subnets (one per AZ) where broker nodes are placed."
}

variable "security_group_ids" {
  type        = list(string)
  description = "Security group ids for the broker nodes (typically the MSK tier SG from the security_groups module)."
}

variable "kafka_version" {
  type        = string
  description = "MSK Kafka version."
  default     = "3.6.0"
}

variable "number_of_broker_nodes" {
  type        = number
  description = "Total broker node count, must be a multiple of the number of AZs used. Default is one broker per AZ (2 AZs); raise it to increase throughput headroom for EC-ESC-03, at additional cost."
  default     = 2
}

variable "broker_instance_type" {
  type        = string
  description = "Broker instance type."
  default     = "kafka.m5.large"
}

variable "ebs_volume_size" {
  type        = number
  description = "EBS volume size in GB per broker, sized for durable log retention (BusEventos, ColaPagos, TopicoTelemetria)."
  default     = 100
}

variable "kms_key_arn" {
  type        = string
  description = "ARN of the CMK used to encrypt data at rest on the brokers."
}

variable "client_broker_encryption" {
  type        = string
  description = "In-transit encryption between clients and brokers."
  default     = "TLS"
}

variable "iam_client_authentication_enabled" {
  type        = bool
  description = "Enable SASL/IAM client authentication (client_authentication.sasl.iam). Default true so consumer groups authenticate with IAM roles instead of long-lived credentials."
  default     = true
}

variable "auto_create_topics_enable" {
  type        = string
  description = "Kafka broker property auto.create.topics.enable. Kept false by default so BusEventos, ColaPagos and TopicoTelemetria are provisioned deliberately, not implicitly on first publish."
  default     = "false"
}

variable "default_replication_factor" {
  type        = string
  description = "Kafka broker property default.replication.factor."
  default     = "3"
}

variable "min_insync_replicas" {
  type        = string
  description = "Kafka broker property min.insync.replicas, paired with acks=all producers to give the exactly-once processing guarantee required by EC-ESC-03."
  default     = "2"
}

variable "log_retention_hours" {
  type        = string
  description = "Kafka broker property log.retention.hours. High by default for durable retention on BusEventos/ColaPagos/TopicoTelemetria."
  default     = "168"
}

variable "num_partitions" {
  type        = string
  description = "Kafka broker property num.partitions (default topic partition count), sized to parallelize consumer groups and absorb backpressure per EC-ESC-03."
  default     = "6"
}

variable "enable_logging" {
  type        = bool
  description = "Enable broker logging to a CloudWatch log group created by this module."
  default     = true
}

variable "log_retention_in_days" {
  type        = number
  description = "CloudWatch log group retention in days for broker logs."
  default     = 14
}

variable "enhanced_monitoring" {
  type        = string
  description = "MSK enhanced monitoring level (DEFAULT, PER_BROKER, PER_TOPIC_PER_BROKER, PER_TOPIC_PER_PARTITION)."
  default     = "PER_TOPIC_PER_BROKER"
}

variable "open_monitoring_enabled" {
  type        = bool
  description = "Enable open monitoring with Prometheus JMX and node exporters, scraped by the Prometheus/Grafana stack from the diagram."
  default     = true
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into all taggable resources."
  default     = {}
}
