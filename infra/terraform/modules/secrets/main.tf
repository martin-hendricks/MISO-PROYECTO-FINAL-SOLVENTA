locals {
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags
  )

  # External providers shown in the deployment diagram (adapters integrate
  # with each of these outside the VPC).
  external_providers = [
    "open_finance",
    "open_data",
    "kyc_aml",
    "pasarela_pago",
    "firma_electronica",
    "telemetria_iot",
    "reaseguro_acord",
  ]
}

# --- Database credentials ---

resource "aws_secretsmanager_secret" "polizas_db" {
  name                    = "${var.project_name}-${var.environment}-polizas-db-credentials"
  description             = "Credenciales de conexion a DBPolizas (RDS PostgreSQL)"
  kms_key_id              = var.kms_key_id
  recovery_window_in_days = var.recovery_window_in_days

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-polizas-db-credentials" })
}

resource "aws_secretsmanager_secret_version" "polizas_db" {
  count = var.polizas_db_credentials != null ? 1 : 0

  secret_id = aws_secretsmanager_secret.polizas_db.id
  secret_string = jsonencode({
    username = var.polizas_db_credentials.username
    password = var.polizas_db_credentials.password
    host     = try(var.polizas_db_credentials.host, null)
    port     = try(var.polizas_db_credentials.port, null)
    dbname   = try(var.polizas_db_credentials.dbname, null)
  })
}

resource "aws_secretsmanager_secret" "siniestros_db" {
  name                    = "${var.project_name}-${var.environment}-siniestros-db-credentials"
  description             = "Credenciales de conexion a DBSiniestros (RDS PostgreSQL)"
  kms_key_id              = var.kms_key_id
  recovery_window_in_days = var.recovery_window_in_days

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-siniestros-db-credentials" })
}

resource "aws_secretsmanager_secret_version" "siniestros_db" {
  count = var.siniestros_db_credentials != null ? 1 : 0

  secret_id = aws_secretsmanager_secret.siniestros_db.id
  secret_string = jsonencode({
    username = var.siniestros_db_credentials.username
    password = var.siniestros_db_credentials.password
    host     = try(var.siniestros_db_credentials.host, null)
    port     = try(var.siniestros_db_credentials.port, null)
    dbname   = try(var.siniestros_db_credentials.dbname, null)
  })
}

# DBCompartida aloja los esquemas de los microservicios sin instancia propia
# (cotización, identidad, consentimiento, pagos, paramétrico, perfilamiento,
# socios, analítica, notificaciones). Un solo secreto con las credenciales
# maestras; el aislamiento por esquema/rol de cada microservicio se gestiona
# fuera de Terraform (ver infra/terraform/README.md).
resource "aws_secretsmanager_secret" "compartida_db" {
  name                    = "${var.project_name}-${var.environment}-compartida-db-credentials"
  description             = "Credenciales de conexion a DBCompartida (RDS PostgreSQL)"
  kms_key_id              = var.kms_key_id
  recovery_window_in_days = var.recovery_window_in_days

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-compartida-db-credentials" })
}

resource "aws_secretsmanager_secret_version" "compartida_db" {
  count = var.compartida_db_credentials != null ? 1 : 0

  secret_id = aws_secretsmanager_secret.compartida_db.id
  secret_string = jsonencode({
    username = var.compartida_db_credentials.username
    password = var.compartida_db_credentials.password
    host     = try(var.compartida_db_credentials.host, null)
    port     = try(var.compartida_db_credentials.port, null)
    dbname   = try(var.compartida_db_credentials.dbname, null)
  })
}

# --- External provider credentials (adapters: open_finance, open_data, kyc_aml,
# pasarela_pago, firma_electronica, telemetria_iot, reaseguro_acord) ---

resource "aws_secretsmanager_secret" "external_providers" {
  for_each = toset(local.external_providers)

  name                    = "${var.project_name}-${var.environment}-${each.key}-credentials"
  description             = "Credenciales del proveedor externo ${each.key}"
  kms_key_id              = var.kms_key_id
  recovery_window_in_days = var.recovery_window_in_days

  tags = merge(local.common_tags, {
    Name     = "${var.project_name}-${var.environment}-${each.key}-credentials"
    Provider = each.key
  })
}
