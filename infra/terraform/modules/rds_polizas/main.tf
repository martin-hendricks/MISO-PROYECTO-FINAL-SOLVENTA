# Resuelve la AZ real de cada subred de datos para poder fijar
# availability_zone explícita en la primaria y la réplica (ver el comentario
# en aws_db_instance.read_replica: sin esto, RDS puede colocar ambas en la
# misma zona y la redundancia activa de EC-LAT-10 deja de ser real).
#
# for_each itera sobre índices (0, 1, ...), no sobre los IDs de subred en sí:
# en este ambiente esos IDs son outputs del módulo network creado en el mismo
# apply, así que durante el plan son "known after apply" y un for_each/toset
# sobre ellos directamente no converge (el mismo problema ya resuelto en
# modules/observability). El número de subredes sí es estático.
data "aws_subnet" "data_subnets" {
  for_each = { for idx in range(length(var.private_data_subnet_ids)) : tostring(idx) => var.private_data_subnet_ids[idx] }
  id       = each.value
}

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

  # Lista de AZs ordenada de forma estable (no depende del orden de
  # evaluación de for_each) a partir de las subredes de datos recibidas.
  data_subnet_azs = sort([for s in data.aws_subnet.data_subnets : s.availability_zone])

  primary_az = local.data_subnet_azs[0]
  replica_az = local.data_subnet_azs[length(local.data_subnet_azs) > 1 ? 1 : 0]
}

resource "random_password" "master" {
  length  = 32
  special = false
}

resource "aws_db_subnet_group" "this" {
  name       = "${var.project_name}-${var.environment}-polizas-db-subnets"
  subnet_ids = var.private_data_subnet_ids

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-polizas-db-subnets" })
}

resource "aws_db_parameter_group" "this" {
  name   = "${var.project_name}-${var.environment}-polizas-pg16"
  family = "postgres16"

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-polizas-pg16" })
}

# DBPolizas — redundancia ACTIVA (nodo "DBPolizas" del diagrama de despliegue).
#
# La wiki de arquitectura (Vista de despliegue — AWS) es explícita: "Mantener
# múltiples copias de datos — redundancia ACTIVA: réplica de lectura en AZ-b
# que atiende tráfico en producción", bajo el escenario EC-LAT-10
# (p95 <= 150 ms, RPO <= 30 s). La razón de negocio es que el problema aquí es
# volumen de lectura -- web y móvil consultando repetidamente la misma
# cobertura vigente -- así que en vez de dejar el standby ocioso se pone a
# servir ese tráfico de lectura, aceptando el desfase acotado por el RPO.
# Ver aws_db_instance.read_replica más abajo: expone su propio endpoint como
# output de primera clase porque SÍ participa del tráfico de producción.
resource "aws_db_instance" "this" {
  identifier = "${var.project_name}-${var.environment}-polizas-primary"

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

  # Fijada explícitamente a la primera AZ de las subredes de datos: así la
  # réplica (abajo) puede fijarse a una AZ distinta de forma determinística,
  # en vez de depender de que RDS "normalmente" elija otra zona.
  availability_zone = var.multi_az ? null : local.primary_az

  allocated_storage     = var.allocated_storage
  max_allocated_storage = local.storage_autoscaling ? var.max_allocated_storage : null
  storage_encrypted     = true
  storage_type          = "gp3"
  kms_key_id            = var.kms_key_id

  multi_az                  = var.multi_az
  publicly_accessible       = false
  backup_retention_period   = var.backup_retention_period
  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.project_name}-${var.environment}-polizas-final"
  deletion_protection       = var.deletion_protection

  performance_insights_enabled          = var.performance_insights_enabled
  performance_insights_kms_key_id       = var.performance_insights_enabled ? var.kms_key_id : null
  performance_insights_retention_period = var.performance_insights_enabled ? 7 : null

  auto_minor_version_upgrade = true
  copy_tags_to_snapshot      = true

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-polizas-primary" })
}

# Réplica de lectura ACTIVA: atiende tráfico real de producción (web y móvil
# consultando la cobertura vigente), en una AZ distinta a la primaria para
# que también funcione como redundancia zonal. No es un standby pasivo: su
# endpoint se expone como output de primera clase (reader_endpoint) para que
# los servicios de consulta lo usen directamente.
resource "aws_db_instance" "read_replica" {
  count = var.create_read_replica ? 1 : 0

  identifier          = "${var.project_name}-${var.environment}-polizas-replica"
  replicate_source_db = aws_db_instance.this.identifier

  instance_class = var.replica_instance_class

  # Fijada explícitamente a una AZ distinta de la primaria. Sin esto, AWS
  # elige la zona de la réplica y puede coincidir con la de la primaria: el
  # comentario anterior de este módulo afirmaba que RDS "siempre" la coloca
  # en otra zona, lo cual no es cierto. local.replica_az ya resuelve a una AZ
  # distinta de local.primary_az cuando hay al menos dos subredes de datos
  # (el caso esperado en este ambiente); con una sola subred, ambas AZs
  # coinciden y la redundancia zonal real depende de ampliar las subredes.
  availability_zone   = local.replica_az
  publicly_accessible = false

  storage_encrypted = true
  kms_key_id        = var.kms_key_id
  storage_type      = "gp3"

  performance_insights_enabled          = var.performance_insights_enabled
  performance_insights_kms_key_id       = var.performance_insights_enabled ? var.kms_key_id : null
  performance_insights_retention_period = var.performance_insights_enabled ? 7 : null

  vpc_security_group_ids = var.vpc_security_group_ids

  skip_final_snapshot = true
  deletion_protection = false

  auto_minor_version_upgrade = true
  copy_tags_to_snapshot      = true

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-polizas-replica" })
}
