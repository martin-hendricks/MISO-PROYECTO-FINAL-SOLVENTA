# MSK (Kafka) — BusEventos, ColaPagos, TopicoTelemetria (nodo "MSK (Kafka)"
# del diagrama de despliegue). Las anotaciones del diagrama son
# "contrapresión, retención duradera, grupo consumidores", bajo el escenario
# EC-ESC-03: absorber >= 1.000.000 eventos en 10 min con procesamiento
# exactamente una vez. Esto se traduce en las server_properties de la
# configuration (auto.create.topics.enable=false, replication factor y
# min.insync.replicas para el guardado exactamente-una-vez con productores
# acks=all, log.retention.hours para retención duradera, num.partitions para
# paralelizar los grupos de consumidores) y en encryption_in_transit/IAM para
# que cada consumer group se autentique de forma segura.

locals {
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags
  )
}

resource "aws_cloudwatch_log_group" "broker_logs" {
  count = var.enable_logging ? 1 : 0

  name              = "/aws/msk/${var.project_name}-${var.environment}"
  retention_in_days = var.log_retention_in_days

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-msk-logs" })
}

resource "aws_msk_configuration" "this" {
  name           = "${var.project_name}-${var.environment}-msk-config"
  kafka_versions = [var.kafka_version]

  server_properties = <<-PROPERTIES
    auto.create.topics.enable=${var.auto_create_topics_enable}
    default.replication.factor=${var.default_replication_factor}
    min.insync.replicas=${var.min_insync_replicas}
    log.retention.hours=${var.log_retention_hours}
    num.partitions=${var.num_partitions}
  PROPERTIES
}

resource "aws_msk_cluster" "this" {
  cluster_name           = "${var.project_name}-${var.environment}-msk"
  kafka_version          = var.kafka_version
  number_of_broker_nodes = var.number_of_broker_nodes

  broker_node_group_info {
    instance_type   = var.broker_instance_type
    client_subnets  = var.private_data_subnet_ids
    security_groups = var.security_group_ids

    storage_info {
      ebs_storage_info {
        volume_size = var.ebs_volume_size
      }
    }
  }

  configuration_info {
    arn      = aws_msk_configuration.this.arn
    revision = aws_msk_configuration.this.latest_revision
  }

  encryption_info {
    encryption_at_rest_kms_key_arn = var.kms_key_arn

    encryption_in_transit {
      client_broker = var.client_broker_encryption
      in_cluster    = true
    }
  }

  client_authentication {
    sasl {
      iam = var.iam_client_authentication_enabled
    }
  }

  enhanced_monitoring = var.enhanced_monitoring

  open_monitoring {
    prometheus {
      jmx_exporter {
        enabled_in_broker = var.open_monitoring_enabled
      }
      node_exporter {
        enabled_in_broker = var.open_monitoring_enabled
      }
    }
  }

  dynamic "logging_info" {
    for_each = var.enable_logging ? [1] : []
    content {
      broker_logs {
        cloudwatch_logs {
          enabled   = true
          log_group = aws_cloudwatch_log_group.broker_logs[0].name
        }
      }
    }
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-msk" })
}
