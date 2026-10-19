output "secret_arns" {
  value = merge(
    {
      polizas_db    = aws_secretsmanager_secret.polizas_db.arn
      siniestros_db = aws_secretsmanager_secret.siniestros_db.arn
      compartida_db = aws_secretsmanager_secret.compartida_db.arn
    },
    { for name, secret in aws_secretsmanager_secret.external_providers : name => secret.arn }
  )
  description = "Map of secret name (polizas_db, siniestros_db, compartida_db, and each external provider) to its Secrets Manager ARN."
}

output "polizas_db_secret_arn" {
  value       = aws_secretsmanager_secret.polizas_db.arn
  description = "ARN of the DBPolizas credentials secret."
}

output "siniestros_db_secret_arn" {
  value       = aws_secretsmanager_secret.siniestros_db.arn
  description = "ARN of the DBSiniestros credentials secret."
}

output "compartida_db_secret_arn" {
  value       = aws_secretsmanager_secret.compartida_db.arn
  description = "ARN of the DBCompartida master credentials secret."
}
