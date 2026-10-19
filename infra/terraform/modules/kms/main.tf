data "aws_caller_identity" "current" {}

locals {
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags
  )

  # One CMK per data domain shown in the deployment diagram encrypted by KMS.
  # service_principals: AWS services allowed to use the key (in addition to
  # account root and IAM policies), keyed by domain.
  key_domains = {
    rds = {
      description        = "CMK for RDS (DBPolizas, DBSiniestros) encryption at rest"
      service_principals = ["rds.amazonaws.com"]
    }
    msk = {
      description        = "CMK for MSK (BusEventos, ColaPagos, TopicoTelemetria) encryption at rest"
      service_principals = ["kafka.amazonaws.com"]
    }
    redis = {
      description        = "CMK for ElastiCache Redis (CacheOF, CacheOD) encryption at rest"
      service_principals = ["elasticache.amazonaws.com"]
    }
    s3 = {
      description = "CMK for S3 (evidencia de siniestros) encryption at rest"
      # Esta CMK se reutiliza también para cifrar los CloudWatch Log Groups
      # (observability y la integración del API Gateway): sin
      # logs.amazonaws.com como principal, CreateLogGroup falla con
      # AccessDeniedException ("The specified KMS key does not exist or is
      # not allowed to be used"), porque CloudWatch Logs necesita permiso
      # explícito de la llave, no solo el permiso IAM del caller.
      service_principals = ["s3.amazonaws.com", "logs.amazonaws.com"]
    }
    secrets = {
      description        = "CMK for Secrets Manager (credenciales de BD y terceros) encryption at rest"
      service_principals = ["secretsmanager.amazonaws.com"]
    }
    eks = {
      description        = "CMK for EKS Kubernetes secrets encryption at rest"
      service_principals = ["eks.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "key" {
  for_each = local.key_domains

  statement {
    sid    = "EnableRootAccountFullAccess"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    actions   = ["kms:*"]
    resources = ["*"]
  }

  statement {
    sid    = "AllowServiceUseOfTheKey"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = each.value.service_principals
    }

    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:DescribeKey",
    ]

    resources = ["*"]
  }

  statement {
    sid    = "AllowServiceToCreateGrant"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = each.value.service_principals
    }

    actions   = ["kms:CreateGrant"]
    resources = ["*"]

    condition {
      test     = "Bool"
      variable = "kms:GrantIsForAWSResource"
      values   = ["true"]
    }
  }
}

resource "aws_kms_key" "this" {
  for_each = local.key_domains

  description             = each.value.description
  deletion_window_in_days = var.deletion_window_in_days
  enable_key_rotation     = true
  policy                  = data.aws_iam_policy_document.key[each.key].json

  tags = merge(local.common_tags, {
    Name   = "${var.project_name}-${var.environment}-kms-${each.key}"
    Domain = each.key
  })
}

resource "aws_kms_alias" "this" {
  for_each = local.key_domains

  name          = "alias/${var.project_name}-${var.environment}-${each.key}"
  target_key_id = aws_kms_key.this[each.key].key_id
}
