-- Extensión local de ms-cotizacion sobre el DDL oficial (db/schema/04_ms_cotizacion.sql).
-- No modifica el archivo oficial: lo complementa de forma aditiva y no destructiva.
-- factor_riesgo/factor_riesgo_origen: degradación auditable del adaptador de perfil
-- (HU-5/SOLV-98) — si el factor fue real o de respaldo, nunca invisible.
ALTER TABLE ms_cotizacion.oferta_seguro
    ADD COLUMN factor_riesgo        NUMERIC(6,4) NOT NULL DEFAULT 1.0,
    ADD COLUMN factor_riesgo_origen TEXT NOT NULL DEFAULT 'respaldo'
        CHECK (factor_riesgo_origen IN ('real', 'respaldo'));
