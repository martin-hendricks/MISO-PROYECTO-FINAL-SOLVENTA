-- ms_suscripcion: decisión de suscripción sobre una solicitud y un perfil.
-- Base: db/schema/06_ms_suscripcion.sql. Requiere PostgreSQL 13+ (gen_random_uuid() nativo).

CREATE SCHEMA IF NOT EXISTS ms_suscripcion;

CREATE TABLE IF NOT EXISTS ms_suscripcion.suscripcion (
    suscripcion_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    solicitud_id    UUID        NOT NULL,
    perfil_id       UUID        NOT NULL,
    decision        TEXT        NOT NULL CHECK (decision IN ('ACEPTADA', 'RECHAZADA')),
    motivo          TEXT,
    evaluada_en     TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Una sola decisión por solicitud: hace idempotente la evaluación (HU-13).
    CONSTRAINT uq_suscripcion_solicitud UNIQUE (solicitud_id)
);

COMMENT ON COLUMN ms_suscripcion.suscripcion.solicitud_id IS 'ref lógica -> ms_cotizacion.solicitud_cotizacion.solicitud_id';
COMMENT ON COLUMN ms_suscripcion.suscripcion.perfil_id    IS 'ref lógica -> ms_perfilamiento.perfil_riesgo.perfil_id';

CREATE INDEX IF NOT EXISTS ix_suscripcion_perfil ON ms_suscripcion.suscripcion (perfil_id);

CREATE TABLE IF NOT EXISTS ms_suscripcion.outbox_evento (
    id           UUID PRIMARY KEY,
    tipo         TEXT NOT NULL,
    agregado_id  UUID NOT NULL,
    payload      JSONB NOT NULL,
    creado_en    TIMESTAMPTZ NOT NULL DEFAULT now(),
    publicado_en TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_outbox_evento_pendiente
    ON ms_suscripcion.outbox_evento (creado_en) WHERE publicado_en IS NULL;
