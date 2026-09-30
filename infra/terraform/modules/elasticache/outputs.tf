output "replication_group_id" {
  value       = aws_elasticache_replication_group.this.id
  description = "Replication group id."
}

output "primary_endpoint_address" {
  value       = aws_elasticache_replication_group.this.primary_endpoint_address
  description = "Primary (writer) endpoint. Null when cluster_mode_enabled is true; use the configuration endpoint from the provider data source in that case."
}

output "reader_endpoint_address" {
  value       = aws_elasticache_replication_group.this.reader_endpoint_address
  description = "Reader endpoint address for read-scaling across replicas."
}

output "port" {
  value       = aws_elasticache_replication_group.this.port
  description = "Port the cache clusters listen on."
}

output "auth_token" {
  value       = local.auth_token
  sensitive   = true
  description = "Redis AUTH token used by CacheOF/CacheOD clients."
}
