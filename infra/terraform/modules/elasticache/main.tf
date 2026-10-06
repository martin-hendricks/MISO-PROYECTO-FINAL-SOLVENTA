# ElastiCache Redis — CacheOF (Open Finance) y CacheOD (Open Data), TTL por
# fuente. Protegen el presupuesto de latencia de los adaptadores externos
# (nodo "ElastiCache Redis" del diagrama de despliegue): cada adaptador fija
# su propio TTL vía var.parameters o en la capa de aplicación; este módulo
# provee un único replication group reutilizable por ambos caches.

locals {
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags
  )

  parameter_family = "redis7"
}

resource "random_password" "auth_token" {
  count = var.auth_token == "" ? 1 : 0

  length  = 32
  special = false
}

locals {
  auth_token = var.auth_token != "" ? var.auth_token : random_password.auth_token[0].result
}

resource "aws_elasticache_subnet_group" "this" {
  name       = "${var.project_name}-${var.environment}-redis-subnets"
  subnet_ids = var.private_data_subnet_ids

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-redis-subnets" })
}

resource "aws_elasticache_parameter_group" "this" {
  name   = "${var.project_name}-${var.environment}-redis7"
  family = local.parameter_family

  dynamic "parameter" {
    for_each = var.parameters
    content {
      name  = parameter.key
      value = parameter.value
    }
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-redis7" })
}

resource "aws_elasticache_replication_group" "this" {
  replication_group_id = "${var.project_name}-${var.environment}-redis"
  description          = "Solventa ${var.environment} Redis - CacheOF / CacheOD"

  engine         = "redis"
  engine_version = var.engine_version
  node_type      = var.node_type
  port           = var.port

  parameter_group_name = aws_elasticache_parameter_group.this.name
  subnet_group_name    = aws_elasticache_subnet_group.this.name
  security_group_ids   = var.security_group_ids

  automatic_failover_enabled = var.automatic_failover_enabled
  multi_az_enabled           = var.multi_az_enabled

  num_cache_clusters      = var.cluster_mode_enabled ? null : var.num_cache_clusters
  num_node_groups         = var.cluster_mode_enabled ? var.num_node_groups : null
  replicas_per_node_group = var.cluster_mode_enabled ? var.replicas_per_node_group : null

  at_rest_encryption_enabled = true
  kms_key_id                 = var.kms_key_id
  transit_encryption_enabled = true
  auth_token                 = local.auth_token

  snapshot_retention_limit = var.snapshot_retention_limit

  apply_immediately = true

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-redis" })
}
