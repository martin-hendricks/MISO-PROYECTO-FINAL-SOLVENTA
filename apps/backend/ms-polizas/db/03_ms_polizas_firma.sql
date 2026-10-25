-- ms_polizas: constancia de firma electrónica simulada (HU-17).
-- Incremental sobre db/01_ms_polizas.sql. Guarda cada resultado de firma,
-- exitoso o no, para que la emisión sea auditable. Una oferta puede tener
-- varias constancias (un rechazo y un reintento); la vigente es la más reciente.

CREATE TABLE IF NOT EXISTS ms_polizas.constancia_firma (
    constancia_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    oferta_id      UUID NOT NULL,
    exitosa        BOOLEAN NOT NULL,
    motivo         TEXT,
    firma_hash     TEXT,
    firmada_en     TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Una firma exitosa lleva su hash; una fallida, su motivo.
    CONSTRAINT ck_constancia_resultado CHECK (
        (exitosa AND firma_hash IS NOT NULL) OR (NOT exitosa AND motivo IS NOT NULL)
    )
);

COMMENT ON COLUMN ms_polizas.constancia_firma.oferta_id  IS 'ref lógica -> ms_cotizacion.oferta_seguro.oferta_id';
COMMENT ON COLUMN ms_polizas.constancia_firma.firma_hash IS 'Hash que devuelve el adaptador de firma; se copia a poliza.firma_hash al emitir';

CREATE INDEX IF NOT EXISTS ix_constancia_firma_oferta ON ms_polizas.constancia_firma (oferta_id, firmada_en DESC);
