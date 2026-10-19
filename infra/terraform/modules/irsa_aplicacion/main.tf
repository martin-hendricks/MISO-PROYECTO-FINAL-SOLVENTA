# IRSA para los workloads de aplicación.
#
# El módulo eks_addons crea roles IRSA para los add-ons del clúster (ALB
# Controller, Cluster Autoscaler, External Secrets). Este módulo hace lo mismo
# para los microservicios que hablan con AWS: cada uno recibe un rol propio con
# permisos mínimos, asumible únicamente por su ServiceAccount.
#
# La trust policy es lo que impide que un componente use el rol de otro: la
# condición sobre `sub` ata el rol a un namespace y un nombre de ServiceAccount
# concretos, así que el token de `analitica` no sirve para asumir el rol de
# `ms-pagos` aunque ambos vivan en el mismo clúster.
#
# El output role_arns alimenta el campo serviceAccount.roleArn de los values de
# Helm en infra/k8s/values/.

locals {
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags
  )

  # Componentes que escriben y leen evidencia de siniestros en S3.
  s3_consumers = {
    "ms-siniestros" = {
      service_account = "ms-siniestros"
    }
  }

  # Componentes que producen o consumen del bus de eventos. Cada uno declara los
  # tópicos que toca, de modo que la política no conceda acceso al clúster MSK
  # entero.
  msk_consumers = {
    "ms-parametrico" = {
      service_account = "ms-parametrico"
      topics          = ["TopicoTelemetria"]
      consumer_groups = ["ms-parametrico"]
    }
    "ms-pagos" = {
      service_account = "ms-pagos"
      topics          = ["ColaPagos"]
      consumer_groups = ["ms-pagos"]
    }
    "analitica" = {
      service_account = "analitica"
      topics          = ["BusEventos"]
      consumer_groups = ["analitica"]
    }
    "notificaciones" = {
      service_account = "notificaciones"
      topics          = ["BusEventos"]
      consumer_groups = ["notificaciones"]
    }
  }

  # Unión de ambos conjuntos: todo componente que necesita un rol.
  all_components = merge(
    { for k, v in local.s3_consumers : k => v.service_account },
    { for k, v in local.msk_consumers : k => v.service_account },
  )
}

# ---------------------------------------------------------------------------
# Trust policy — una por componente, atada a su ServiceAccount
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "assume_role" {
  for_each = local.all_components

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [var.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${var.oidc_provider_url}:sub"
      values   = ["system:serviceaccount:${var.namespace}:${each.value}"]
    }

    condition {
      test     = "StringEquals"
      variable = "${var.oidc_provider_url}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "this" {
  for_each = local.all_components

  name               = "${var.project_name}-${var.environment}-${each.key}-irsa"
  description        = "IRSA role for the ${each.key} workload in the ${var.namespace} namespace."
  assume_role_policy = data.aws_iam_policy_document.assume_role[each.key].json

  tags = merge(local.common_tags, {
    Name      = "${var.project_name}-${var.environment}-${each.key}-irsa"
    Component = each.key
  })
}

# ---------------------------------------------------------------------------
# S3 — evidencia de siniestros
# ---------------------------------------------------------------------------

# ms-siniestros sube la evidencia que el cliente adjunta a una reclamación y la
# vuelve a leer para mostrarla. No se le concede borrado: la evidencia de un
# siniestro es dato auditable, y su expiración la gobierna la lifecycle policy
# del bucket, no la aplicación.
data "aws_iam_policy_document" "s3_evidencias" {
  for_each = local.s3_consumers

  statement {
    sid    = "ObjectReadWrite"
    effect = "Allow"

    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:AbortMultipartUpload",
    ]

    resources = ["${var.evidencias_bucket_arn}/*"]
  }

  statement {
    sid    = "BucketList"
    effect = "Allow"

    actions = [
      "s3:ListBucket",
      "s3:GetBucketLocation",
    ]

    resources = [var.evidencias_bucket_arn]
  }

  # El bucket está cifrado con CMK, así que sin estos permisos las subidas
  # fallan aunque los de S3 estén bien.
  statement {
    sid    = "KmsForBucketEncryption"
    effect = "Allow"

    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey",
    ]

    resources = [var.s3_kms_key_arn]
  }
}

resource "aws_iam_policy" "s3_evidencias" {
  for_each = local.s3_consumers

  name        = "${var.project_name}-${var.environment}-${each.key}-s3-evidencias"
  description = "Read/write access to the claim evidence bucket for ${each.key}."
  policy      = data.aws_iam_policy_document.s3_evidencias[each.key].json

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "s3_evidencias" {
  for_each = local.s3_consumers

  role       = aws_iam_role.this[each.key].name
  policy_arn = aws_iam_policy.s3_evidencias[each.key].arn
}

# ---------------------------------------------------------------------------
# MSK — bus de eventos con autenticación IAM
# ---------------------------------------------------------------------------

# El clúster MSK usa SASL/IAM, así que la autorización de Kafka se expresa como
# permisos de IAM sobre ARNs de tópico y de grupo de consumidores. Los ARNs se
# derivan del ARN del clúster, que tiene la forma
# arn:aws:kafka:<region>:<account>:cluster/<nombre>/<uuid>.
locals {
  msk_topic_arn_prefix = replace(
    var.msk_cluster_arn,
    "cluster/",
    "topic/"
  )

  msk_group_arn_prefix = replace(
    var.msk_cluster_arn,
    "cluster/",
    "group/"
  )
}

data "aws_iam_policy_document" "msk" {
  for_each = local.msk_consumers

  statement {
    sid       = "ClusterConnect"
    effect    = "Allow"
    actions   = ["kafka-cluster:Connect", "kafka-cluster:DescribeCluster"]
    resources = [var.msk_cluster_arn]
  }

  statement {
    sid    = "TopicAccess"
    effect = "Allow"

    actions = [
      "kafka-cluster:DescribeTopic",
      "kafka-cluster:ReadData",
      "kafka-cluster:WriteData",
    ]

    resources = [
      for t in each.value.topics : "${local.msk_topic_arn_prefix}/${t}"
    ]
  }

  statement {
    sid    = "ConsumerGroupAccess"
    effect = "Allow"

    actions = [
      "kafka-cluster:AlterGroup",
      "kafka-cluster:DescribeGroup",
    ]

    resources = [
      for g in each.value.consumer_groups : "${local.msk_group_arn_prefix}/${g}"
    ]
  }

  # Los datos en reposo de MSK están cifrados con CMK.
  statement {
    sid       = "KmsForClusterEncryption"
    effect    = "Allow"
    actions   = ["kms:Decrypt", "kms:GenerateDataKey"]
    resources = [var.msk_kms_key_arn]
  }
}

resource "aws_iam_policy" "msk" {
  for_each = local.msk_consumers

  name        = "${var.project_name}-${var.environment}-${each.key}-msk"
  description = "MSK IAM access scoped to the topics ${each.key} consumes or produces."
  policy      = data.aws_iam_policy_document.msk[each.key].json

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "msk" {
  for_each = local.msk_consumers

  role       = aws_iam_role.this[each.key].name
  policy_arn = aws_iam_policy.msk[each.key].arn
}
