# ---------------------------------------------------------------------------
# Generales
# ---------------------------------------------------------------------------

variable "aws_region" {
  type        = string
  description = "Región de AWS donde vive el ambiente."
  default     = "us-east-1"
}

variable "project_name" {
  type        = string
  description = "Prefijo corto para nombrar y etiquetar todos los recursos."
  default     = "solventa"
}

variable "environment" {
  type        = string
  description = "Nombre del ambiente. Para HU-78 es 'minimo'."
  default     = "minimo"
}

variable "extra_tags" {
  type        = map(string)
  description = "Etiquetas adicionales que se propagan a todos los módulos."
  default     = {}
}

# ---------------------------------------------------------------------------
# Red
# ---------------------------------------------------------------------------

variable "vpc_cidr" {
  type        = string
  description = "CIDR IPv4 de la VPC."
  default     = "10.0.0.0/16"
}

variable "az_count" {
  type        = number
  description = "Número de zonas de disponibilidad. Mínimo 2 para el multi-AZ activo-activo de EC-DISP-06."
  default     = 2

  validation {
    condition     = var.az_count >= 2
    error_message = "La arquitectura exige al menos dos zonas de disponibilidad (EC-DISP-06, RTO <= 10 min ante falla zonal)."
  }
}

variable "single_nat_gateway" {
  type        = bool
  description = "Un solo NAT gateway compartido en vez de uno por AZ. Abarata el ambiente a costa de que el NAT sea punto único de falla para la salida a internet."
  default     = true
}

variable "enable_flow_logs" {
  type        = bool
  description = "Habilita VPC Flow Logs hacia CloudWatch."
  default     = true
}

# ---------------------------------------------------------------------------
# KMS y secretos
# ---------------------------------------------------------------------------

variable "kms_deletion_window_in_days" {
  type        = number
  description = "Ventana de borrado de las llaves KMS. 7 es el mínimo de AWS y el adecuado para un ambiente destructible."
  default     = 7
}

variable "secrets_recovery_window_in_days" {
  type        = number
  description = "Ventana de recuperación de Secrets Manager. 0 borra de inmediato, necesario para que el destroy de HU-78 deje la cuenta limpia."
  default     = 0
}

# ---------------------------------------------------------------------------
# Bases de datos
# ---------------------------------------------------------------------------

variable "polizas_db_name" {
  type        = string
  description = "Nombre de la base de datos de pólizas."
  default     = "ms_polizas"
}

variable "polizas_db_username" {
  type        = string
  description = "Usuario maestro de la base de datos de pólizas."
  default     = "solventa_polizas"
}

variable "polizas_instance_class" {
  type        = string
  description = "Clase de instancia de la primaria de pólizas."
  default     = "db.t4g.medium"
}

variable "polizas_replica_instance_class" {
  type        = string
  description = "Clase de instancia de la réplica de lectura de pólizas. Esta réplica sirve tráfico real (EC-LAT-10), así que no conviene dimensionarla por debajo de la primaria."
  default     = "db.t4g.medium"
}

variable "polizas_allocated_storage" {
  type        = number
  description = "Almacenamiento inicial en GB de la base de pólizas."
  default     = 20
}

variable "polizas_max_allocated_storage" {
  type        = number
  description = "Techo del autoescalado de almacenamiento de pólizas."
  default     = 100
}

variable "polizas_multi_az" {
  type        = bool
  description = "Multi-AZ en la primaria de pólizas, además de la réplica de lectura."
  default     = true
}

variable "polizas_create_read_replica" {
  type        = bool
  description = "Crea la réplica de lectura ACTIVA de pólizas. Apagarla incumple EC-LAT-10; existe solo para poder abaratar corridas de prueba."
  default     = true
}

variable "siniestros_db_name" {
  type        = string
  description = "Nombre de la base de datos de siniestros."
  default     = "ms_siniestros"
}

variable "siniestros_db_username" {
  type        = string
  description = "Usuario maestro de la base de datos de siniestros."
  default     = "solventa_siniestros"
}

variable "siniestros_instance_class" {
  type        = string
  description = "Clase de instancia de siniestros."
  default     = "db.t4g.medium"
}

variable "siniestros_allocated_storage" {
  type        = number
  description = "Almacenamiento inicial en GB de la base de siniestros."
  default     = 20
}

variable "siniestros_max_allocated_storage" {
  type        = number
  description = "Techo del autoescalado de almacenamiento de siniestros."
  default     = 100
}

variable "compartida_db_name" {
  type        = string
  description = "Nombre de la base de datos compartida (aloja un esquema por microservicio sin instancia propia)."
  default     = "compartida"
}

variable "compartida_db_username" {
  type        = string
  description = "Usuario maestro de la base de datos compartida."
  default     = "solventa_compartida"
}

variable "compartida_instance_class" {
  type        = string
  description = "Clase de instancia de la base compartida. Sin redundancia (ver PLAN.md), así que su tamaño es la única palanca de capacidad disponible."
  default     = "db.t4g.medium"
}

variable "compartida_allocated_storage" {
  type        = number
  description = "Almacenamiento inicial en GB de la base compartida."
  default     = 20
}

variable "compartida_max_allocated_storage" {
  type        = number
  description = "Techo del autoescalado de almacenamiento de la base compartida."
  default     = 100
}

variable "rds_backup_retention_period" {
  type        = number
  description = "Días de retención de backups en ambas bases."
  default     = 7
}

variable "rds_skip_final_snapshot" {
  type        = bool
  description = "Omite el snapshot final al destruir. true en el ambiente mínimo para que el destroy sea limpio; en producción debe ser false."
  default     = true
}

variable "rds_deletion_protection" {
  type        = bool
  description = "Protección contra borrado de las instancias RDS. false en el ambiente mínimo por el criterio de destructibilidad de HU-78."
  default     = false
}

# ---------------------------------------------------------------------------
# Caché y bus de eventos
# ---------------------------------------------------------------------------

variable "redis_node_type" {
  type        = string
  description = "Tipo de nodo de ElastiCache Redis (CacheOF / CacheOD)."
  default     = "cache.t4g.medium"
}

variable "redis_num_cache_clusters" {
  type        = number
  description = "Número de nodos del grupo de replicación de Redis. 2 da failover automático entre AZs."
  default     = 2
}

variable "redis_snapshot_retention_limit" {
  type        = number
  description = "Días de retención de snapshots de Redis. 0 en el ambiente mínimo: la caché es reconstruible."
  default     = 0
}

variable "kafka_version" {
  type        = string
  description = "Versión de Kafka del clúster MSK."
  default     = "3.6.0"
}

variable "msk_number_of_broker_nodes" {
  type        = number
  description = "Número de brokers de MSK. Debe ser múltiplo del número de AZs de las subredes de datos."
  default     = 2
}

variable "msk_broker_instance_type" {
  type        = string
  description = "Tipo de instancia de los brokers de MSK."
  default     = "kafka.m5.large"
}

variable "msk_ebs_volume_size" {
  type        = number
  description = "Volumen EBS en GB por broker, dimensionado para la retención duradera de BusEventos, ColaPagos y TopicoTelemetria."
  default     = 100
}

# ---------------------------------------------------------------------------
# EKS
# ---------------------------------------------------------------------------

variable "kubernetes_version" {
  type        = string
  description = "Versión de Kubernetes del clúster EKS."
  default     = "1.31"
}

variable "eks_endpoint_public_access" {
  type        = bool
  description = "Expone el endpoint de la API de Kubernetes a internet. Necesario para operar el clúster sin bastión ni VPN."
  default     = true
}

variable "eks_public_access_cidrs" {
  type        = list(string)
  description = "CIDRs que pueden alcanzar el endpoint público de la API. El default es abierto: restringirlo a las IPs del equipo antes de dejar el ambiente arriba."
  default     = ["0.0.0.0/0"]
}

variable "node_group_a_instance_types" {
  type        = list(string)
  description = "Tipos de instancia del Grupo A (ms-cotizacion + ms-perfilamiento). Cómputo intensivo: los motores de rating y riesgo escalan verticalmente para ganar los primeros segundos de la rampa."
  default     = ["c6i.xlarge"]
}

variable "node_group_a_min_size" {
  type        = number
  description = "Nodos mínimos del Grupo A."
  default     = 2
}

variable "node_group_a_desired_size" {
  type        = number
  description = "Nodos deseados del Grupo A al crear. Después lo gobierna el Cluster Autoscaler."
  default     = 2
}

variable "node_group_a_max_size" {
  type        = number
  description = "Nodos máximos del Grupo A. Es el techo que sostiene el pico de EC-ESC-01 (50.000 cot/min)."
  default     = 6
}

variable "node_group_b_instance_types" {
  type        = list(string)
  description = "Tipos de instancia del Grupo B (resto de microservicios, BFFs y adaptadores). Propósito general."
  default     = ["m6i.large"]
}

variable "node_group_b_min_size" {
  type        = number
  description = "Nodos mínimos del Grupo B."
  default     = 2
}

variable "node_group_b_desired_size" {
  type        = number
  description = "Nodos deseados del Grupo B al crear."
  default     = 2
}

variable "node_group_b_max_size" {
  type        = number
  description = "Nodos máximos del Grupo B."
  default     = 6
}

variable "enable_external_secrets" {
  type        = bool
  description = "Instala External Secrets Operator para que los pods lean de Secrets Manager sin credenciales estáticas."
  default     = true
}

variable "ecr_force_delete" {
  type        = bool
  description = "Permite borrar repositorios ECR con imágenes dentro. true en el ambiente mínimo por destructibilidad."
  default     = true
}

# ---------------------------------------------------------------------------
# Borde
# ---------------------------------------------------------------------------

variable "certificate_arn" {
  type        = string
  description = "ARN del certificado ACM para el listener HTTPS del ALB. Vacío deja solo HTTP, que es lo esperable mientras no haya dominio."
  default     = ""
}

variable "health_check_path" {
  type        = string
  description = "Ruta de health check del target group del ALB."
  default     = "/health"
}

variable "alb_enable_deletion_protection" {
  type        = bool
  description = "Protección contra borrado del ALB. false por destructibilidad."
  default     = false
}

variable "cloudfront_price_class" {
  type        = string
  description = "Clase de precio de CloudFront. PriceClass_100 cubre Norteamérica y Europa al menor costo."
  default     = "PriceClass_100"
}

variable "waf_rate_limit" {
  type        = number
  description = "Límite de peticiones por IP en ventana de 5 minutos antes de que WAF bloquee."
  default     = 2000
}

variable "s3_force_destroy" {
  type        = bool
  description = "Permite destruir los buckets con objetos dentro. true en el ambiente mínimo; en producción debe ser false, sobre todo en el de evidencia de siniestros."
  default     = true
}

# ---------------------------------------------------------------------------
# Observabilidad
# ---------------------------------------------------------------------------

variable "log_retention_days" {
  type        = number
  description = "Días de retención de los log groups de los microservicios."
  default     = 14
}

variable "alarm_email" {
  type        = string
  description = "Correo que recibe las alarmas de CloudWatch. Vacío no crea suscripción."
  default     = ""
}

variable "enable_managed_prometheus" {
  type        = bool
  description = "Crea un workspace de Amazon Managed Prometheus. Apagado por defecto porque tiene costo propio y Prometheus puede correr dentro del clúster."
  default     = false
}

variable "k8s_namespace" {
  type        = string
  description = "Namespace de Kubernetes donde corren los microservicios. Forma parte de la trust policy de IRSA, así que debe coincidir con infra/k8s/platform/namespace.yaml."
  default     = "solventa"
}
