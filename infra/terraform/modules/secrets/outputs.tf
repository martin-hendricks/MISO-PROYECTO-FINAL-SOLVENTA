output "secret_arns" {
  value = merge(
    {
      polizas_db        = aws_secretsmanager_secret.polizas_db.arn
      siniestros_db     = aws_secretsmanager_secret.siniestros_db.arn
      compartida_db     = aws_secretsmanager_secret.compartida_db.arn
      bff_web_token     = aws_secretsmanager_secret.bff_web_token.arn
      bff_movil_token   = aws_secretsmanager_secret.bff_movil_token.arn
      siniestros_config = aws_secretsmanager_secret.siniestros_config.arn
      grafana_admin     = aws_secretsmanager_secret.grafana_admin.arn
    },
    { for name, secret in aws_secretsmanager_secret.external_providers : name => secret.arn }
  )
  description = "Map of secret name (polizas_db, siniestros_db, compartida_db, bff_web_token, bff_movil_token, siniestros_config, grafana_admin, and each external provider) to its Secrets Manager ARN."
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

output "bff_web_token_secret_arn" {
  value       = aws_secretsmanager_secret.bff_web_token.arn
  description = "ARN of the shared JWT signing secret (SOLVENTA_TOKEN_SECRET) used by bff-web, bff-movil, and the core services that verify those tokens."
}

output "bff_movil_token_secret_arn" {
  value       = aws_secretsmanager_secret.bff_movil_token.arn
  description = "ARN of the unused former bff-movil JWT secret. bff-movil signs with bff_web_token_secret_arn."
}

output "grafana_admin_secret_arn" {
  value       = aws_secretsmanager_secret.grafana_admin.arn
  description = "ARN of the Grafana admin credentials secret (GF_SECURITY_ADMIN_USER/PASSWORD)."
}
