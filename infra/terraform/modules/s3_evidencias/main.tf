locals {
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags
  )

  bucket_suffix = length(var.bucket_suffix) > 0 ? var.bucket_suffix : random_id.suffix.hex
  bucket_name   = lower("${var.project_name}-${var.environment}-evidencias-siniestros-${local.bucket_suffix}")

  cors_enabled = length(var.cors_allowed_origins) > 0
}

resource "random_id" "suffix" {
  byte_length = 4
}

# --- Bucket de evidencia de siniestros ---
# Dato sensible de clientes: versionado obligatorio (la evidencia no se debe
# perder), cifrado con CMK, sin acceso público.

resource "aws_s3_bucket" "this" {
  bucket        = local.bucket_name
  force_destroy = var.force_destroy

  tags = merge(local.common_tags, { Name = local.bucket_name })
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Ciclo de vida: transición a STANDARD_IA y luego GLACIER, y expiración de
# versiones no actuales para no acumular costo indefinidamente.
resource "aws_s3_bucket_lifecycle_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    id     = "evidencias-lifecycle"
    status = "Enabled"

    filter {}

    transition {
      days          = var.transition_ia_days
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = var.transition_glacier_days
      storage_class = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_expiration_days
    }
  }
}

# Deniega explícitamente cualquier tráfico no cifrado (HTTP en lugar de HTTPS).
data "aws_iam_policy_document" "this" {
  statement {
    sid    = "DenyInsecureTransport"
    effect = "Deny"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions   = ["s3:*"]
    resources = [aws_s3_bucket.this.arn, "${aws_s3_bucket.this.arn}/*"]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "this" {
  bucket = aws_s3_bucket.this.id
  policy = data.aws_iam_policy_document.this.json
}

# CORS opcional: la app móvil sube evidencia de siniestros directamente al bucket.
resource "aws_s3_bucket_cors_configuration" "this" {
  count = local.cors_enabled ? 1 : 0

  bucket = aws_s3_bucket.this.id

  cors_rule {
    allowed_origins = var.cors_allowed_origins
    allowed_methods = var.cors_allowed_methods
    allowed_headers = var.cors_allowed_headers
    max_age_seconds = var.cors_max_age_seconds
  }
}
