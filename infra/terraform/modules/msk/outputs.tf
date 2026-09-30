output "cluster_arn" {
  value       = aws_msk_cluster.this.arn
  description = "ARN of the MSK cluster."
}

output "cluster_name" {
  value       = aws_msk_cluster.this.cluster_name
  description = "Name of the MSK cluster."
}

output "bootstrap_brokers_tls" {
  value       = aws_msk_cluster.this.bootstrap_brokers_tls
  description = "Bootstrap broker string for TLS client connections."
}

output "bootstrap_brokers_sasl_iam" {
  value       = aws_msk_cluster.this.bootstrap_brokers_sasl_iam
  description = "Bootstrap broker string for SASL/IAM client connections, used by consumer groups authenticating with IAM roles."
}

output "zookeeper_connect_string" {
  value       = aws_msk_cluster.this.zookeeper_connect_string
  description = "Zookeeper connection string for the cluster."
}

output "configuration_arn" {
  value       = aws_msk_configuration.this.arn
  description = "ARN of the MSK configuration (server_properties: BusEventos/ColaPagos/TopicoTelemetria retention and partitioning)."
}
