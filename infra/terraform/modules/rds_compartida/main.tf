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
  name       = "${var.project_name}-${var.environment}-compartida-db-subnets"
  subnet_ids = var.private_data_subnet_ids

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-compartida-db-subnets" })
}

resource "aws_db_parameter_group" "this" {
  name   = "${var.project_name}-${var.environment}-compartida-pg16"
  family = "postgres16"

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-compartida-pg16" })
}

# DBCompartida — SIN redundancia (no está en el diagrama de despliegue VC-003).
#
# La wiki solo define dos políticas de redundancia, cada una ligada a un
# problema de negocio concreto: activa para pólizas (volumen de lectura) y
# pasiva para siniestros (continuidad sin staleness del estado de una
# reclamación). Esta tercera instancia aloja los esquemas de los demás
# microservicios del monorepo (cotización, identidad, consentimiento, pagos,
# paramétrico, perfilamiento, socios, analítica, notificaciones), ninguno de
# los cuales tenía instancia propia en el plan original ni corresponde a
# ninguna de esas dos categorías. Forzarla dentro de "activa" o "pasiva"
# inventaría una tercera política que la wiki no sostiene, así que se deja
# explícitamente sin Multi-AZ y sin réplica de lectura: solo backups
# automáticos. Si la caída de una zona se vuelve un requisito para alguno de
# estos esquemas, ese microservicio debería moverse a su propia instancia con
# la política de redundancia que le corresponda, no forzar una aquí.
resource "aws_db_instance" "this" {
  identifier = "${var.project_name}-${var.environment}-compartida-primary"

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

  # Sin redundancia a propósito: ver el comentario arriba.
  multi_az = false

  publicly_accessible       = false
  backup_retention_period   = var.backup_retention_period
  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.project_name}-${var.environment}-compartida-final"
  deletion_protection       = var.deletion_protection

  performance_insights_enabled          = var.performance_insights_enabled
  performance_insights_kms_key_id       = var.performance_insights_enabled ? var.kms_key_id : null
  performance_insights_retention_period = var.performance_insights_enabled ? 7 : null

  auto_minor_version_upgrade = true
  copy_tags_to_snapshot      = true

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-compartida-primary" })
}
