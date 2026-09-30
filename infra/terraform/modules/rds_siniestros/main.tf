locals {
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags
  )

  storage_autoscaling = var.max_allocated_storage > var.allocated_storage
}

resource "random_password" "master" {
  length  = 32
  special = false
}

resource "aws_db_subnet_group" "this" {
  name       = "${var.project_name}-${var.environment}-siniestros-db-subnets"
  subnet_ids = var.private_data_subnet_ids

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-siniestros-db-subnets" })
}

resource "aws_db_parameter_group" "this" {
  name   = "${var.project_name}-${var.environment}-siniestros-pg16"
  family = "postgres16"

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-siniestros-pg16" })
}

# DBSiniestros — redundancia PASIVA (nodo "DBSiniestros" del diagrama de
# despliegue).
#
# La wiki de arquitectura es explícita: "redundancia PASIVA: standby Multi-AZ
# en AZ-b que NO sirve tráfico", bajo los escenarios EC-DISP-06 / EC-DISP-07
# (RTO <= 10 min ante falla zonal). multi_az se fuerza a true (no se expone
# como variable) porque el standby de Multi-AZ nativo de RDS es exactamente
# la primitiva correcta aquí: réplica síncrona que solo se promueve a primaria
# cuando AWS detecta la falla de la zona, y mientras tanto no atiende tráfico.
#
# A propósito, este módulo NO crea un aws_db_instance de réplica de lectura
# (a diferencia de rds_polizas). Esa es la decisión de arquitectura: dejar que
# una réplica sirviera lecturas introduciría staleness sobre un dato que el
# cliente interpreta como el estado vigente de su reclamación (¿fue aprobada?
# ¿en qué etapa está?). Ese staleness es aceptable para consultar cobertura
# vigente de pólizas (EC-LAT-10), pero no para el estado de un siniestro, así
# que la redundancia se mantiene completamente fuera del camino de tráfico y
# solo se promueve cuando el Monitor detecta la caída de la zona.
resource "aws_db_instance" "this" {
  identifier = "${var.project_name}-${var.environment}-siniestros-primary"

  engine               = "postgres"
  engine_version       = var.engine_version
  instance_class       = var.instance_class
  db_name              = var.db_name
  username             = var.db_username
  password             = random_password.master.result
  port                 = 5432
  parameter_group_name = aws_db_parameter_group.this.name

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = var.vpc_security_group_ids

  allocated_storage     = var.allocated_storage
  max_allocated_storage = local.storage_autoscaling ? var.max_allocated_storage : null
  storage_encrypted     = true
  storage_type          = "gp3"
  kms_key_id            = var.kms_key_id

  # Forzado: este es el punto central de la decisión de redundancia pasiva.
  multi_az = true

  publicly_accessible       = false
  backup_retention_period   = var.backup_retention_period
  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.project_name}-${var.environment}-siniestros-final"
  deletion_protection       = var.deletion_protection

  performance_insights_enabled          = var.performance_insights_enabled
  performance_insights_kms_key_id       = var.performance_insights_enabled ? var.kms_key_id : null
  performance_insights_retention_period = var.performance_insights_enabled ? 7 : null

  auto_minor_version_upgrade = true
  copy_tags_to_snapshot      = true

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-siniestros-primary" })
}
