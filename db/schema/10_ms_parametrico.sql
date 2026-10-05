-- ms_parametrico: eventos paramétricos disparados por telemetría (EC-ESC-03).
-- Requiere PostgreSQL 13+ (gen_random_uuid() nativo).

CREATE SCHEMA IF NOT EXISTS ms_parametrico;

CREATE TABLE ms_parametrico.evento_parametrico (
    evento_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evento_externo_id  TEXT          NOT NULL,
    reclamacion_id     UUID,
    tipo_evento        TEXT          NOT NULL,
    -- Excepción a NUMERIC(14,2): son mediciones de telemetría, no montos.
    umbral             NUMERIC(14,4) NOT NULL,
    valor_observado    NUMERIC(14,4) NOT NULL,
    disparado_en       TIMESTAMPTZ   NOT NULL DEFAULT now(),
    -- Deduplicación del evento de telemetría: procesamiento exactamente una vez (EC-ESC-03).
    CONSTRAINT uq_evento_externo UNIQUE (evento_externo_id)
);

COMMENT ON COLUMN ms_parametrico.evento_parametrico.reclamacion_id IS 'ref lógica opcional -> ms_siniestros.reclamacion.reclamacion_id';

CREATE INDEX ix_evento_parametrico_reclamacion ON ms_parametrico.evento_parametrico (reclamacion_id) WHERE reclamacion_id IS NOT NULL;
