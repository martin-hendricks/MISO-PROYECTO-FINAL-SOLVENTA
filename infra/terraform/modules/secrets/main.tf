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
    # URL de conexión ya armada, para microservicios (ms-cotizacion, etc.)
    # cuya app espera una única variable DATABASE_URL en vez de componer la
    # URL a partir de host/port/user/password por separado. El chart
    # genérico solo sabe mapear una clave de un Secret a una variable de
    # entorno; esta clave evita tener que cambiar esa app por cada
    # consumidor de DBCompartida.
    database_url = "postgresql+asyncpg://${var.compartida_db_credentials.username}:${var.compartida_db_credentials.password}@${try(var.compartida_db_credentials.host, "")}:${try(var.compartida_db_credentials.port, "")}/${try(var.compartida_db_credentials.dbname, "")}"
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

# Placeholder NO funcional, solo para que el contenedor arranque en un
# ambiente nuevo sin depender de un `aws secretsmanager put-secret-value`
# manual (lo que pasaba hasta ahora: ms-cotizacion fallaba con
# CreateContainerConfigError -> Secret does not exist hasta que alguien
# cargaba algo a mano). El valor "PENDIENTE_<provider>" es deliberadamente
# obvio para que, si alguien lo ve en un log o en la respuesta de la API
# del proveedor real, quede claro que nadie cargó la credencial real
# todavía -- no es un secreto débil, es un secreto inexistente a propósito.
resource "aws_secretsmanager_secret_version" "external_providers" {
  for_each = var.seed_external_provider_placeholders ? toset(local.external_providers) : []

  secret_id = aws_secretsmanager_secret.external_providers[each.key].id
  secret_string = jsonencode({
    clientId     = "PENDIENTE_${each.key}"
    clientSecret = "PENDIENTE_${each.key}"
  })

  lifecycle {
    # Una vez que alguien carga la credencial real (a mano, fuera de
    # Terraform), un `terraform apply` posterior NO debe pisarla de vuelta
    # con el placeholder. Terraform sigue creando esta versión si no existe
    # (ambiente nuevo), pero no vuelve a forzar el placeholder sobre un
    # valor real ya cargado.
    ignore_changes = [secret_string]
  }
}

# --- bff-web token secret ---
#
# SOLVENTA_TOKEN_SECRET firma los JWT que bff-web emite para las sesiones
# web (apps/backend/bff-web/app/dependencies.py) -- no es la credencial de
# ningún proveedor externo, es puramente interno al cluster, así que no
# necesita ser una credencial real conocida por nadie: alcanza con que sea
# estable (el mismo valor sobrevive cada deploy, para no invalidar las
# sesiones activas) y no quede commiteado.
resource "random_password" "bff_web_token_secret" {
  length  = 48
  special = false
}

resource "aws_secretsmanager_secret" "bff_web_token" {
  name                    = "${var.project_name}-${var.environment}-bff-web-token"
  description             = "Secreto usado por bff-web para firmar/validar los JWT de sesion (SOLVENTA_TOKEN_SECRET)"
  kms_key_id              = var.kms_key_id
  recovery_window_in_days = var.recovery_window_in_days

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-bff-web-token" })
}

resource "aws_secretsmanager_secret_version" "bff_web_token" {
  secret_id = aws_secretsmanager_secret.bff_web_token.id
  # La clave del JSON es el nombre exacto de la env var (SOLVENTA_TOKEN_SECRET)
  # para que el ExternalSecret la proyecte vía dataFrom.extract sin necesidad
  # de listar `claves` en infra/k8s/values/bff-web.yaml.
  secret_string = jsonencode({ SOLVENTA_TOKEN_SECRET = random_password.bff_web_token_secret.result })

  lifecycle {
    ignore_changes = [secret_string]
  }
}
