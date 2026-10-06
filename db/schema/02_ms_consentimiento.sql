-- ms_consentimiento: consentimientos de uso de datos (Open Finance / Open Data).
-- Requiere PostgreSQL 13+ (gen_random_uuid() nativo).

CREATE SCHEMA IF NOT EXISTS ms_consentimiento;

CREATE TABLE ms_consentimiento.consentimiento_datos (
    consentimiento_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id         UUID        NOT NULL,
    fuente             TEXT        NOT NULL,
    estado             TEXT        NOT NULL,
    otorgado_en        TIMESTAMPTZ NOT NULL DEFAULT now(),
    revocado_en        TIMESTAMPTZ
);

COMMENT ON COLUMN ms_consentimiento.consentimiento_datos.usuario_id IS 'ref lógica -> ms_identidad.usuario.usuario_id';

CREATE INDEX ix_consentimiento_usuario ON ms_consentimiento.consentimiento_datos (usuario_id);
