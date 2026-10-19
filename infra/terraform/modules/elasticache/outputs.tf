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

output "member_cluster_ids" {
  value       = aws_elasticache_replication_group.this.member_clusters
  description = "Real per-node cache cluster ids (e.g. <replication_group_id>-001), the value CloudWatch's CacheClusterId dimension actually expects. replication_group_id itself is not a valid value for that dimension."
}
