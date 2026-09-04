CREATE SCHEMA IF NOT EXISTS siniestros_r;

CREATE TABLE siniestros_r.siniestro_estado (
    siniestro_id   BIGINT PRIMARY KEY,
    cliente_id     BIGINT      NOT NULL,
    version        INTEGER     NOT NULL,
    ocurrido_en    TIMESTAMPTZ NOT NULL,   -- timestamp del evento origen
    proyectado_en  TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload        JSONB       NOT NULL    -- respuesta completa preconstruida
);

CREATE INDEX idx_estado_cliente ON siniestros_r.siniestro_estado(cliente_id);
