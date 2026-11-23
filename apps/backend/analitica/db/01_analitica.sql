-- analitica: contadores agregados de eventos de ciclo de vida de póliza.
-- PostgreSQL 13+. Idempotente: se puede reaplicar.

CREATE SCHEMA IF NOT EXISTS analitica;

CREATE TABLE IF NOT EXISTS analitica.conteo_eventos (
    id        SERIAL PRIMARY KEY,
    tipo      TEXT        NOT NULL,
    fecha     DATE        NOT NULL,
    cantidad  INTEGER     NOT NULL DEFAULT 0,
    CONSTRAINT uq_conteo_tipo_fecha UNIQUE (tipo, fecha)
);

-- Un registro por evento_id consumido: evita incrementar dos veces el mismo
-- conteo si el mensaje del bus llega repetido (reintento de Kafka, replay).
CREATE TABLE IF NOT EXISTS analitica.evento_procesado (
    evento_id TEXT PRIMARY KEY
);

CREATE INDEX IF NOT EXISTS ix_conteo_eventos_fecha
    ON analitica.conteo_eventos (fecha);

COMMENT ON TABLE analitica.conteo_eventos IS 'Contador agregado de eventos de BusEventos por tipo y fecha (HU-68)';
COMMENT ON TABLE analitica.evento_procesado IS 'Idempotencia del consumidor: un evento_id solo incrementa un contador una vez';
