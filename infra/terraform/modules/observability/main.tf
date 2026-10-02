locals {
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags
  )

  log_group_map = { for name in var.log_groups : name => "/${var.project_name}/${var.environment}/${name}" }

  alarm_email_enabled = length(var.alarm_email) > 0
  alb_enabled         = var.enable_alb_alarms
  msk_enabled         = var.enable_msk_alarms

  # El for_each/count de cada bloque de alarmas no puede depender de
  # alb_arn_suffix/rds_instance_ids/etc. directamente: en este ambiente esos
  # valores son outputs de recursos creados en el mismo apply (el ALB, las
  # instancias RDS...), así que durante el plan son "known after apply" y
  # Terraform no puede decidir cuántas instancias crear a partir de ellos.
  #
  # La solución es la que el propio error de Terraform sugiere: separar
  # "cuántas alarmas crear" (una clave estática, conocida ahora, vía
  # rds_alarm_keys / elasticache_alarm_keys) de "qué recurso monitorea cada
  # una" (un valor que solo se conoce tras el apply). El for_each solo ve la
  # clave estática; el ID real correspondiente se resuelve por posición en
  # rds_instance_ids / elasticache_cluster_ids dentro del propio recurso.
}

# =============================================================================
# CloudWatch log groups — uno por microservicio/componente del monorepo
# =============================================================================

resource "aws_cloudwatch_log_group" "microservices" {
  for_each = local.log_group_map

  name              = each.value
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn

  tags = merge(local.common_tags, { Name = each.value, Microservice = each.key })
}

# =============================================================================
# SNS — tópico de alarmas con suscripción por email opcional
# =============================================================================

resource "aws_sns_topic" "alarms" {
  name = "${var.project_name}-${var.environment}-alarms"

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-alarms" })
}

resource "aws_sns_topic_subscription" "alarms_email" {
  count = local.alarm_email_enabled ? 1 : 0

  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# =============================================================================
# Alarmas — ALB (latencia p95, EC-LAT-03; y 5xx)
# =============================================================================

resource "aws_cloudwatch_metric_alarm" "alb_p95_latency" {
  count = local.alb_enabled ? 1 : 0

  alarm_name          = "${var.project_name}-${var.environment}-alb-p95-latency"
  alarm_description   = "ALB p95 TargetResponseTime above threshold (EC-LAT-03)."
  namespace           = "AWS/ApplicationELB"
  metric_name         = "TargetResponseTime"
  extended_statistic  = "p95"
  comparison_operator = "GreaterThanThreshold"
  threshold           = var.alb_p95_latency_threshold_seconds
  evaluation_periods  = var.alarm_evaluation_periods
  period              = var.alarm_period_seconds
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-alb-p95-latency" })
}

resource "aws_cloudwatch_metric_alarm" "alb_5xx" {
  count = local.alb_enabled ? 1 : 0

  alarm_name          = "${var.project_name}-${var.environment}-alb-5xx"
  alarm_description   = "ALB-generated 5xx responses above threshold."
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HTTPCode_ELB_5XX_Count"
  statistic           = "Sum"
  comparison_operator = "GreaterThanThreshold"
  threshold           = var.alb_5xx_threshold
  evaluation_periods  = var.alarm_evaluation_periods
  period              = var.alarm_period_seconds
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-alb-5xx" })
}

# =============================================================================
# Alarmas — RDS CPU alta (DBPolizas, DBSiniestros)
# =============================================================================

resource "aws_cloudwatch_metric_alarm" "rds_high_cpu" {
  # for_each itera sobre las claves estáticas (conocidas en el plan); el ID
  # real de la instancia, que solo se conoce tras el apply, se resuelve por
  # posición dentro de "dimensions", no en el for_each.
  for_each = toset(var.rds_alarm_keys)

  alarm_name          = "${var.project_name}-${var.environment}-rds-${each.key}-cpu"
  alarm_description   = "RDS instance ${each.key} CPUUtilization above threshold."
  namespace           = "AWS/RDS"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  comparison_operator = "GreaterThanThreshold"
  threshold           = var.rds_cpu_threshold_percent
  evaluation_periods  = var.alarm_evaluation_periods
  period              = var.alarm_period_seconds
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_ids[index(var.rds_alarm_keys, each.key)]
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-rds-${each.key}-cpu" })
}

# =============================================================================
# Alarmas — ElastiCache memoria alta y evictions (CacheOF, CacheOD)
# =============================================================================

resource "aws_cloudwatch_metric_alarm" "elasticache_high_memory" {
  # Igual que en rds_high_cpu: for_each sobre claves estáticas, el ID real del
  # clúster se resuelve por posición dentro de "dimensions".
  for_each = toset(var.elasticache_alarm_keys)

  alarm_name          = "${var.project_name}-${var.environment}-redis-${each.key}-memory"
  alarm_description   = "ElastiCache cluster ${each.key} DatabaseMemoryUsagePercentage above threshold."
  namespace           = "AWS/ElastiCache"
  metric_name         = "DatabaseMemoryUsagePercentage"
  statistic           = "Average"
  comparison_operator = "GreaterThanThreshold"
  threshold           = var.elasticache_memory_threshold_percent
  evaluation_periods  = var.alarm_evaluation_periods
  period              = var.alarm_period_seconds
  treat_missing_data  = "notBreaching"

  dimensions = {
    CacheClusterId = var.elasticache_cluster_ids[index(var.elasticache_alarm_keys, each.key)]
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-redis-${each.key}-memory" })
}

resource "aws_cloudwatch_metric_alarm" "elasticache_evictions" {
  for_each = toset(var.elasticache_alarm_keys)

  alarm_name          = "${var.project_name}-${var.environment}-redis-${each.key}-evictions"
  alarm_description   = "ElastiCache cluster ${each.key} Evictions above threshold."
  namespace           = "AWS/ElastiCache"
  metric_name         = "Evictions"
  statistic           = "Sum"
  comparison_operator = "GreaterThanThreshold"
  threshold           = var.elasticache_evictions_threshold
  evaluation_periods  = var.alarm_evaluation_periods
  period              = var.alarm_period_seconds
  treat_missing_data  = "notBreaching"

  dimensions = {
    CacheClusterId = var.elasticache_cluster_ids[index(var.elasticache_alarm_keys, each.key)]
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-redis-${each.key}-evictions" })
}

# =============================================================================
# Alarmas — MSK: lag de consumidores y uso de disco (BusEventos, ColaPagos,
# TopicoTelemetria comparten cluster)
# =============================================================================

resource "aws_cloudwatch_metric_alarm" "msk_consumer_lag" {
  count = local.msk_enabled ? 1 : 0

  alarm_name          = "${var.project_name}-${var.environment}-msk-consumer-lag"
  alarm_description   = "MSK consumer group MaxOffsetLag above threshold (backpressure, EC-ESC-03)."
  namespace           = "AWS/Kafka"
  metric_name         = "MaxOffsetLag"
  statistic           = "Maximum"
  comparison_operator = "GreaterThanThreshold"
  threshold           = var.msk_consumer_lag_threshold
  evaluation_periods  = var.alarm_evaluation_periods
  period              = var.alarm_period_seconds
  treat_missing_data  = "notBreaching"

  dimensions = {
    "Cluster Name" = var.msk_cluster_name
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-msk-consumer-lag" })
}

resource "aws_cloudwatch_metric_alarm" "msk_disk_usage" {
  count = local.msk_enabled ? 1 : 0

  alarm_name          = "${var.project_name}-${var.environment}-msk-disk-usage"
  alarm_description   = "MSK broker KafkaDataLogsDiskUsed percentage above threshold."
  namespace           = "AWS/Kafka"
  metric_name         = "KafkaDataLogsDiskUsed"
  statistic           = "Average"
  comparison_operator = "GreaterThanThreshold"
  threshold           = var.msk_disk_usage_threshold_percent
  evaluation_periods  = var.alarm_evaluation_periods
  period              = var.alarm_period_seconds
  treat_missing_data  = "notBreaching"

  dimensions = {
    "Cluster Name" = var.msk_cluster_name
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-msk-disk-usage" })
}

# =============================================================================
# Dashboard — agrupa las métricas de ALB, RDS, ElastiCache y MSK
# =============================================================================

resource "aws_cloudwatch_dashboard" "this" {
  dashboard_name = "${var.project_name}-${var.environment}-observability"

  dashboard_body = jsonencode({
    widgets = concat(
      local.alb_enabled ? [
        {
          type   = "metric"
          x      = 0
          y      = 0
          width  = 12
          height = 6
          properties = {
            title  = "ALB - p95 latency (EC-LAT-03)"
            view   = "timeSeries"
            region = data.aws_region.current.name
            metrics = [
              ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", var.alb_arn_suffix, { stat = "p95" }]
            ]
          }
        },
        {
          type   = "metric"
          x      = 12
          y      = 0
          width  = 12
          height = 6
          properties = {
            title  = "ALB - 5xx count"
            view   = "timeSeries"
            region = data.aws_region.current.name
            metrics = [
              ["AWS/ApplicationELB", "HTTPCode_ELB_5XX_Count", "LoadBalancer", var.alb_arn_suffix, { stat = "Sum" }]
            ]
          }
        }
      ] : [],
      length(var.rds_alarm_keys) > 0 ? [
        {
          type   = "metric"
          x      = 0
          y      = 6
          width  = 12
          height = 6
          properties = {
            title  = "RDS - CPUUtilization"
            view   = "timeSeries"
            region = data.aws_region.current.name
            metrics = [
              for id in var.rds_instance_ids : ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", id]
            ]
          }
        }
      ] : [],
      length(var.elasticache_alarm_keys) > 0 ? [
        {
          type   = "metric"
          x      = 12
          y      = 6
          width  = 12
          height = 6
          properties = {
            title  = "ElastiCache - memory % / evictions"
            view   = "timeSeries"
            region = data.aws_region.current.name
            metrics = concat(
              [for id in var.elasticache_cluster_ids : ["AWS/ElastiCache", "DatabaseMemoryUsagePercentage", "CacheClusterId", id]],
              [for id in var.elasticache_cluster_ids : ["AWS/ElastiCache", "Evictions", "CacheClusterId", id]]
            )
          }
        }
      ] : [],
      local.msk_enabled ? [
        {
          type   = "metric"
          x      = 0
          y      = 12
          width  = 12
          height = 6
          properties = {
            title  = "MSK - consumer lag / disk usage"
            view   = "timeSeries"
            region = data.aws_region.current.name
            metrics = [
              ["AWS/Kafka", "MaxOffsetLag", "Cluster Name", var.msk_cluster_name],
              ["AWS/Kafka", "KafkaDataLogsDiskUsed", "Cluster Name", var.msk_cluster_name]
            ]
          }
        }
      ] : []
    )
  })
}

data "aws_region" "current" {}

# =============================================================================
# Amazon Managed Service for Prometheus (AMP) — opcional, tiene costo fijo
# =============================================================================

resource "aws_prometheus_workspace" "this" {
  count = var.enable_managed_prometheus ? 1 : 0

  alias = "${var.project_name}-${var.environment}-amp"

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-amp" })
}
