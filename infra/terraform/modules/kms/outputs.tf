output "key_arns" {
  value       = { for domain, key in aws_kms_key.this : domain => key.arn }
  description = "Map of data domain (rds, msk, redis, s3, secrets, eks) to its CMK ARN."
}

output "key_ids" {
  value       = { for domain, key in aws_kms_key.this : domain => key.key_id }
  description = "Map of data domain (rds, msk, redis, s3, secrets, eks) to its CMK key ID."
}

output "rds_key_arn" {
  value       = aws_kms_key.this["rds"].arn
  description = "CMK ARN for RDS (DBPolizas, DBSiniestros)."
}

output "msk_key_arn" {
  value       = aws_kms_key.this["msk"].arn
  description = "CMK ARN for MSK (BusEventos, ColaPagos, TopicoTelemetria)."
}

output "redis_key_arn" {
  value       = aws_kms_key.this["redis"].arn
  description = "CMK ARN for ElastiCache Redis (CacheOF, CacheOD)."
}

output "s3_key_arn" {
  value       = aws_kms_key.this["s3"].arn
  description = "CMK ARN for S3 (evidencia de siniestros)."
}

output "secrets_key_arn" {
  value       = aws_kms_key.this["secrets"].arn
  description = "CMK ARN for Secrets Manager."
}

output "eks_key_arn" {
  value       = aws_kms_key.this["eks"].arn
  description = "CMK ARN for EKS Kubernetes secrets encryption at rest."
}
