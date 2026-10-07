-- Extensión local de ms-cotizacion sobre el DDL oficial (db/schema/04_ms_cotizacion.sql).
-- No modifica el archivo oficial: lo complementa de forma aditiva y no destructiva.
-- idempotency_key: soporta el patrón de idempotencia del arquetipo (header Idempotency-Key).
-- datos_riesgo: auditoría de qué se pidió; el DDL oficial no tiene columna para esto.
ALTER TABLE ms_cotizacion.solicitud_cotizacion
    ADD COLUMN idempotency_key TEXT NOT NULL,
    ADD COLUMN datos_riesgo    JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD CONSTRAINT uq_solicitud_idempotency_key UNIQUE (idempotency_key);
