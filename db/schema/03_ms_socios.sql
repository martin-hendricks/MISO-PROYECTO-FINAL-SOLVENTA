-- ms_socios: socios de distribución (canales embebidos).
-- Requiere PostgreSQL 13+ (gen_random_uuid() nativo).

CREATE SCHEMA IF NOT EXISTS ms_socios;

CREATE TABLE ms_socios.socio (
    socio_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre         TEXT    NOT NULL,
    canal          TEXT    NOT NULL,
    estado         TEXT    NOT NULL,
    cuota_mensual  INTEGER NOT NULL
);
