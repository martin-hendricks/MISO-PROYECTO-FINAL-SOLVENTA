-- analitica: eventos de dominio consumidos del bus (consistencia eventual).
-- Requiere PostgreSQL 13+ (gen_random_uuid() nativo).

CREATE SCHEMA IF NOT EXISTS analitica;

CREATE TABLE analitica.evento_analitico (
    evento_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evento_origen_id  UUID        NOT NULL,
    tipo_evento       TEXT        NOT NULL,
    entidad_origen    TEXT        NOT NULL,
    payload           JSONB       NOT NULL,
    ocurrido_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Idempotencia del consumidor: una reentrega de Kafka no duplica el registro (§1.1.4.4, EC-ESC-03).
    CONSTRAINT uq_evento_analitico_origen UNIQUE (evento_origen_id)
);

COMMENT ON COLUMN analitica.evento_analitico.evento_origen_id IS 'id del evento de dominio recibido del bus (outbox_id del productor)';
COMMENT ON COLUMN analitica.evento_analitico.ocurrido_en      IS 'atributo "timestamp" del modelo (VC-004)';

CREATE INDEX ix_evento_analitico_tipo ON analitica.evento_analitico (tipo_evento, ocurrido_en);
