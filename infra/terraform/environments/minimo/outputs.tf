# ---------------------------------------------------------------------------
# Red
# ---------------------------------------------------------------------------

output "vpc_id" {
  value       = module.network.vpc_id
  description = "ID de la VPC de Solventa."
}

output "private_app_subnet_ids" {
  value       = module.network.private_app_subnet_ids
  description = "Subredes privadas de aplicación, donde viven los node groups de EKS."
}

output "private_data_subnet_ids" {
  value       = module.network.private_data_subnet_ids
  description = "Subredes privadas de datos, donde viven RDS, ElastiCache y MSK."
}

# ---------------------------------------------------------------------------
# Cómputo
# ---------------------------------------------------------------------------

output "cluster_name" {
  value       = module.eks.cluster_name
  description = "Nombre del clúster EKS."
}

output "cluster_endpoint" {
  value       = module.eks.cluster_endpoint
  description = "Endpoint de la API de Kubernetes."
}

output "kubeconfig_command" {
  value       = "aws eks update-kubeconfig --name ${module.eks.cluster_name} --region ${var.aws_region}"
  description = "Comando para apuntar kubectl a este clúster, paso previo a aplicar los manifiestos de los microservicios."
}

output "ecr_repository_urls" {
  value       = module.ecr.repository_urls
  description = "URLs de los repositorios ECR por componente, para etiquetar y publicar imágenes."
}

# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------

output "polizas_writer_endpoint" {
  value       = module.rds_polizas.writer_endpoint
  description = "Endpoint de escritura de la base de pólizas."
}

output "polizas_reader_endpoint" {
  value       = module.rds_polizas.reader_endpoint
  description = "Endpoint de la réplica de lectura ACTIVA de pólizas. Las consultas de lectura deben apuntar aquí (EC-LAT-10)."
}

output "siniestros_endpoint" {
  value       = module.rds_siniestros.endpoint
  description = "Endpoint de la base de siniestros. No existe endpoint de lectura: el standby es pasivo por diseño (EC-DISP-06/07)."
}

output "redis_primary_endpoint" {
  value       = module.elasticache.primary_endpoint_address
  description = "Endpoint primario de Redis (CacheOF / CacheOD)."
}

output "msk_bootstrap_brokers_sasl_iam" {
  value       = module.msk.bootstrap_brokers_sasl_iam
  description = "Brokers de MSK con autenticación IAM, para los productores y consumidores del bus de eventos."
}

# ---------------------------------------------------------------------------
# Borde
# ---------------------------------------------------------------------------

output "alb_dns_name" {
  value       = module.alb.alb_dns_name
  description = "DNS del Application Load Balancer."
}

output "cloudfront_domain_name" {
  value       = module.edge.cloudfront_domain_name
  description = "Dominio de CloudFront que sirve la SPA de Angular."
}

output "api_gateway_endpoint" {
  value       = module.edge.api_gateway_endpoint
  description = "Endpoint del API Gateway: punto de entrada de los clientes y de los socios de distribución."
}

output "spa_bucket_name" {
  value       = module.edge.spa_bucket_name
  description = "Bucket donde se publica el build de la SPA de Angular."
}

output "evidencias_bucket_name" {
  value       = module.s3_evidencias.bucket_id
  description = "Bucket de evidencia de siniestros."
}

# ---------------------------------------------------------------------------
# Secretos y observabilidad
# ---------------------------------------------------------------------------

output "secret_arns" {
  value       = module.secrets.secret_arns
  description = "ARNs de los secretos de Secrets Manager, para referenciarlos desde External Secrets."
}

output "alarms_topic_arn" {
  value       = module.observability.sns_topic_arn
  description = "Tópico SNS al que llegan las alarmas de CloudWatch."
}

output "irsa_role_arns" {
  value       = module.irsa_aplicacion.role_arns
  description = "ARN del rol IRSA por componente. Cada valor va en serviceAccount.roleArn del archivo correspondiente de infra/k8s/values/."
}
