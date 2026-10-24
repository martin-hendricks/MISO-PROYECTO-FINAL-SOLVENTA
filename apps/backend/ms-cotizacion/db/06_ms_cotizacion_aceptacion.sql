-- Extensión local de ms-cotizacion (HU-12/SOLV-105): aceptación de la oferta vigente.
-- Aditiva y no destructiva sobre el DDL oficial (db/schema/04_ms_cotizacion.sql).
-- aceptacion_key: Idempotency-Key de la aceptación; el reintento con la misma clave
-- devuelve el resultado original y otra clave sobre una cotización aceptada se rechaza.
-- aceptada_en: momento en que se congeló el precio de la oferta.
ALTER TABLE ms_cotizacion.solicitud_cotizacion
    ADD COLUMN aceptacion_key TEXT,
    ADD COLUMN aceptada_en    TIMESTAMPTZ,
    ADD CONSTRAINT ck_solicitud_aceptacion
        CHECK ((estado = 'aceptada') = (aceptacion_key IS NOT NULL AND aceptada_en IS NOT NULL));
