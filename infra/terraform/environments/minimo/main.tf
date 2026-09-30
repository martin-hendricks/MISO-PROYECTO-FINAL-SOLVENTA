# Ambiente mínimo de producto — HU-78
#
# Composición de la vista de despliegue VC-003 de la wiki. Cada módulo
# corresponde a un nodo del diagrama; la trazabilidad completa está en
# ../../PLAN.md.
#
# Lo que este ambiente NO crea: los Deployments de los 12 microservicios. Esa es
# la frontera acordada — Terraform provisiona la plataforma, los workloads van en
# manifiestos de Kubernetes.

data "aws_availability_zones" "available" {
  state = "available"
}

check "at_least_two_availability_zones" {
  assert {
    condition     = length(data.aws_availability_zones.available.names) >= 2
    error_message = "La arquitectura exige multi-AZ activo-activo (EC-DISP-06): la región elegida debe tener al menos dos zonas habilitadas."
  }
}

locals {
  azs         = slice(data.aws_availability_zones.available.names, 0, var.az_count)
  name_prefix = "${var.project_name}-${var.environment}"

  # El nombre del clúster se calcula aquí y no se toma de module.eks para evitar
  # un ciclo: la VPC necesita el tag kubernetes.io/cluster/<nombre> en sus
  # subredes antes de que exista el clúster que las usa.
  cluster_name = "${local.name_prefix}-eks"
}

# ---------------------------------------------------------------------------
# Base — red, seguridad, llaves y secretos
# ---------------------------------------------------------------------------

module "network" {
  source = "../../modules/network"

  project_name       = var.project_name
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = local.azs
  single_nat_gateway = var.single_nat_gateway
  cluster_name       = local.cluster_name
  enable_flow_logs   = var.enable_flow_logs
  tags               = var.extra_tags
}

module "security_groups" {
  source = "../../modules/security_groups"

  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.network.vpc_id
  vpc_cidr     = module.network.vpc_cidr_block
  tags         = var.extra_tags
}

module "kms" {
  source = "../../modules/kms"

  project_name            = var.project_name
  environment             = var.environment
  deletion_window_in_days = var.kms_deletion_window_in_days
  tags                    = var.extra_tags
}

# Las credenciales las genera cada módulo de RDS y se depositan aquí, de modo
# que los pods las lean vía External Secrets y no haya contraseñas en los
# manifiestos. Terraform resuelve el orden por el grafo de dependencias, no por
# la posición en el archivo.
module "secrets" {
  source = "../../modules/secrets"

  project_name            = var.project_name
  environment             = var.environment
  kms_key_id              = module.kms.secrets_key_arn
  recovery_window_in_days = var.secrets_recovery_window_in_days

  polizas_db_credentials = {
    username = module.rds_polizas.master_username
    password = module.rds_polizas.master_password
    host     = module.rds_polizas.writer_endpoint
    port     = module.rds_polizas.port
    dbname   = module.rds_polizas.db_name
  }

  siniestros_db_credentials = {
    username = module.rds_siniestros.master_username
    password = module.rds_siniestros.master_password
    host     = module.rds_siniestros.endpoint
    port     = module.rds_siniestros.port
    dbname   = module.rds_siniestros.db_name
  }

  tags = var.extra_tags
}

# ---------------------------------------------------------------------------
# Datos — la asimetría de redundancia es deliberada, ver PLAN.md
# ---------------------------------------------------------------------------

# Redundancia ACTIVA: la réplica de lectura sirve tráfico de producción
# (EC-LAT-10, p95 <= 150 ms, RPO <= 30 s).
module "rds_polizas" {
  source = "../../modules/rds_polizas"

  project_name            = var.project_name
  environment             = var.environment
  private_data_subnet_ids = module.network.private_data_subnet_ids
  vpc_security_group_ids  = [module.security_groups.rds_security_group_id]
  db_name                 = var.polizas_db_name
  db_username             = var.polizas_db_username
  instance_class          = var.polizas_instance_class
  replica_instance_class  = var.polizas_replica_instance_class
  allocated_storage       = var.polizas_allocated_storage
  max_allocated_storage   = var.polizas_max_allocated_storage
  multi_az                = var.polizas_multi_az
  create_read_replica     = var.polizas_create_read_replica
  backup_retention_period = var.rds_backup_retention_period
  skip_final_snapshot     = var.rds_skip_final_snapshot
  deletion_protection     = var.rds_deletion_protection
  kms_key_id              = module.kms.rds_key_arn
  tags                    = var.extra_tags
}

# Redundancia PASIVA: el standby Multi-AZ no sirve tráfico y solo se promueve
# ante falla zonal (EC-DISP-06/07, RTO <= 10 min). No hay réplica de lectura por
# diseño: introduciría staleness sobre el estado vigente de una reclamación.
module "rds_siniestros" {
  source = "../../modules/rds_siniestros"

  project_name            = var.project_name
  environment             = var.environment
  private_data_subnet_ids = module.network.private_data_subnet_ids
  vpc_security_group_ids  = [module.security_groups.rds_security_group_id]
  db_name                 = var.siniestros_db_name
  db_username             = var.siniestros_db_username
  instance_class          = var.siniestros_instance_class
  allocated_storage       = var.siniestros_allocated_storage
  max_allocated_storage   = var.siniestros_max_allocated_storage
  backup_retention_period = var.rds_backup_retention_period
  skip_final_snapshot     = var.rds_skip_final_snapshot
  deletion_protection     = var.rds_deletion_protection
  kms_key_id              = module.kms.rds_key_arn
  tags                    = var.extra_tags
}

# CacheOF / CacheOD — protegen el presupuesto de latencia frente a Open Finance
# y Open Data degradados.
module "elasticache" {
  source = "../../modules/elasticache"

  project_name             = var.project_name
  environment              = var.environment
  private_data_subnet_ids  = module.network.private_data_subnet_ids
  security_group_ids       = [module.security_groups.redis_security_group_id]
  node_type                = var.redis_node_type
  num_cache_clusters       = var.redis_num_cache_clusters
  kms_key_id               = module.kms.redis_key_arn
  snapshot_retention_limit = var.redis_snapshot_retention_limit
  tags                     = var.extra_tags
}

# BusEventos, ColaPagos, TopicoTelemetria — contrapresión y retención duradera
# para absorber el pico de EC-ESC-03.
module "msk" {
  source = "../../modules/msk"

  project_name            = var.project_name
  environment             = var.environment
  private_data_subnet_ids = module.network.private_data_subnet_ids
  security_group_ids      = [module.security_groups.msk_security_group_id]
  kafka_version           = var.kafka_version
  number_of_broker_nodes  = var.msk_number_of_broker_nodes
  broker_instance_type    = var.msk_broker_instance_type
  ebs_volume_size         = var.msk_ebs_volume_size
  kms_key_arn             = module.kms.msk_key_arn
  tags                    = var.extra_tags
}

# ---------------------------------------------------------------------------
# Cómputo — EKS con los dos grupos de escalado del diagrama
# ---------------------------------------------------------------------------

module "ecr" {
  source = "../../modules/ecr"

  project_name = var.project_name
  environment  = var.environment
  kms_key_arn  = module.kms.s3_key_arn
  force_delete = var.ecr_force_delete
  tags         = var.extra_tags
}

# Grupo A: ms-cotizacion (MotorRating) + ms-perfilamiento (MotorRiesgo), con
# curvas de carga independientes del resto (EC-ESC-01/02).
# Grupo B: resto de microservicios, BFFs y adaptadores.
module "eks" {
  source = "../../modules/eks"

  project_name           = var.project_name
  environment            = var.environment
  kubernetes_version     = var.kubernetes_version
  vpc_id                 = module.network.vpc_id
  private_app_subnet_ids = module.network.private_app_subnet_ids
  kms_key_arn            = module.kms.eks_key_arn
  node_security_group_ids = [
    module.security_groups.eks_nodes_security_group_id,
  ]
  endpoint_public_access = var.eks_endpoint_public_access
  public_access_cidrs    = var.eks_public_access_cidrs

  node_group_a_instance_types = var.node_group_a_instance_types
  node_group_a_min_size       = var.node_group_a_min_size
  node_group_a_desired_size   = var.node_group_a_desired_size
  node_group_a_max_size       = var.node_group_a_max_size

  node_group_b_instance_types = var.node_group_b_instance_types
  node_group_b_min_size       = var.node_group_b_min_size
  node_group_b_desired_size   = var.node_group_b_desired_size
  node_group_b_max_size       = var.node_group_b_max_size

  tags = var.extra_tags
}

module "eks_addons" {
  source = "../../modules/eks_addons"

  project_name            = var.project_name
  environment             = var.environment
  cluster_name            = module.eks.cluster_name
  oidc_provider_arn       = module.eks.oidc_provider_arn
  oidc_provider_url       = module.eks.oidc_provider_url
  vpc_id                  = module.network.vpc_id
  aws_region              = var.aws_region
  enable_external_secrets = var.enable_external_secrets
  tags                    = var.extra_tags

  depends_on = [module.eks]
}

# IRSA de los workloads: un rol por microservicio que habla con AWS, con
# permisos mínimos y asumible solo por su ServiceAccount. Es lo que permite que
# ms-siniestros escriba en S3 y que los consumidores de MSK se autentiquen por
# IAM, sin llaves estáticas en ningún manifiesto.
#
# Los ARNs que produce alimentan serviceAccount.roleArn en infra/k8s/values/.
module "irsa_aplicacion" {
  source = "../../modules/irsa_aplicacion"

  project_name          = var.project_name
  environment           = var.environment
  namespace             = var.k8s_namespace
  oidc_provider_arn     = module.eks.oidc_provider_arn
  oidc_provider_url     = module.eks.oidc_provider_url
  evidencias_bucket_arn = module.s3_evidencias.bucket_arn
  s3_kms_key_arn        = module.kms.s3_key_arn
  msk_cluster_arn       = module.msk.cluster_arn
  msk_kms_key_arn       = module.kms.msk_key_arn
  tags                  = var.extra_tags
}

# ---------------------------------------------------------------------------
# Borde y almacenamiento
# ---------------------------------------------------------------------------

module "alb" {
  source = "../../modules/alb"

  project_name               = var.project_name
  environment                = var.environment
  vpc_id                     = module.network.vpc_id
  public_subnet_ids          = module.network.public_subnet_ids
  security_group_ids         = [module.security_groups.alb_security_group_id]
  certificate_arn            = var.certificate_arn
  health_check_path          = var.health_check_path
  enable_deletion_protection = var.alb_enable_deletion_protection
  tags                       = var.extra_tags
}

# API Gateway + WAF + CloudFront + S3 de la SPA. El WAF se crea en us-east-1
# porque así lo exige CloudFront.
module "edge" {
  source = "../../modules/edge"

  providers = {
    aws           = aws
    aws.us_east_1 = aws.us_east_1
  }

  project_name             = var.project_name
  environment              = var.environment
  kms_key_arn              = module.kms.s3_key_arn
  alb_dns_name             = module.alb.alb_dns_name
  spa_bucket_force_destroy = var.s3_force_destroy
  cloudfront_price_class   = var.cloudfront_price_class
  waf_rate_limit           = var.waf_rate_limit
  tags                     = var.extra_tags
}

module "s3_evidencias" {
  source = "../../modules/s3_evidencias"

  project_name  = var.project_name
  environment   = var.environment
  kms_key_arn   = module.kms.s3_key_arn
  force_destroy = var.s3_force_destroy
  tags          = var.extra_tags
}

# ---------------------------------------------------------------------------
# Observabilidad — las alarmas se cablean a los recursos ya creados
# ---------------------------------------------------------------------------

module "observability" {
  source = "../../modules/observability"

  project_name       = var.project_name
  environment        = var.environment
  log_retention_days = var.log_retention_days
  kms_key_arn        = module.kms.s3_key_arn
  alarm_email        = var.alarm_email

  alb_arn_suffix = module.alb.alb_arn_suffix

  rds_instance_ids = compact([
    module.rds_polizas.db_instance_id,
    module.rds_siniestros.db_instance_id,
  ])

  elasticache_cluster_ids = [module.elasticache.replication_group_id]
  msk_cluster_name        = module.msk.cluster_name

  enable_managed_prometheus = var.enable_managed_prometheus

  tags = var.extra_tags
}
