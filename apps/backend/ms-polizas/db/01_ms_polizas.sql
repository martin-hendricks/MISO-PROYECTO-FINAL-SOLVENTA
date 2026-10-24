-- ms_polizas: póliza, coberturas y prima.
-- Base: db/schema/07_ms_polizas.sql. Requiere PostgreSQL 13+ (gen_random_uuid() nativo).

CREATE SCHEMA IF NOT EXISTS ms_polizas;

-- Fuente del número de póliza: nunca retrocede, así el número no se reutiliza ni tras una cancelación (HU-16, HU-61).
CREATE SEQUENCE IF NOT EXISTS ms_polizas.poliza_numero_seq;

CREATE TABLE IF NOT EXISTS ms_polizas.poliza (
    poliza_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    oferta_id        UUID NOT NULL,
    usuario_id       UUID NOT NULL,
    numero           TEXT NOT NULL,
    inicio_vigencia  DATE NOT NULL,
    fin_vigencia     DATE NOT NULL,
    estado           TEXT NOT NULL,
    firma_hash       TEXT,
    CONSTRAINT uq_poliza_numero   UNIQUE (numero),
    -- Una sola póliza por oferta aceptada: hace idempotente la emisión (HU-16).
    CONSTRAINT uq_poliza_oferta   UNIQUE (oferta_id),
    CONSTRAINT ck_poliza_vigencia CHECK (fin_vigencia >= inicio_vigencia),
    -- Una póliza EMITIDA siempre lleva su hash de firma legal (VC-007).
    CONSTRAINT ck_poliza_firma    CHECK (estado <> 'EMITIDA' OR firma_hash IS NOT NULL)
);

COMMENT ON COLUMN ms_polizas.poliza.firma_hash IS 'FirmaHash de la póliza; se devuelve como HashFirmaLegal en PolizaEmitidaDTO (VC-007)';
COMMENT ON COLUMN ms_polizas.poliza.oferta_id  IS 'ref lógica -> ms_cotizacion.oferta_seguro.oferta_id';
COMMENT ON COLUMN ms_polizas.poliza.usuario_id IS 'ref lógica -> ms_identidad.usuario.usuario_id';

CREATE INDEX IF NOT EXISTS ix_poliza_usuario ON ms_polizas.poliza (usuario_id);

CREATE TABLE IF NOT EXISTS ms_polizas.cobertura (
    cobertura_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    poliza_id       UUID          NOT NULL REFERENCES ms_polizas.poliza(poliza_id),
    nombre          TEXT          NOT NULL,
    suma_asegurada  NUMERIC(14,2) NOT NULL,
    deducible       NUMERIC(14,2) NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS ix_cobertura_poliza ON ms_polizas.cobertura (poliza_id);

CREATE TABLE IF NOT EXISTS ms_polizas.prima (
    prima_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    poliza_id      UUID          NOT NULL REFERENCES ms_polizas.poliza(poliza_id),
    valor          NUMERIC(14,2) NOT NULL,
    periodicidad   TEXT          NOT NULL,
    proximo_cobro  DATE
);

CREATE INDEX IF NOT EXISTS ix_prima_poliza ON ms_polizas.prima (poliza_id);

CREATE TABLE IF NOT EXISTS ms_polizas.outbox_evento (
    id           UUID PRIMARY KEY,
    tipo         TEXT NOT NULL,
    agregado_id  UUID NOT NULL,
    payload      JSONB NOT NULL,
    creado_en    TIMESTAMPTZ NOT NULL DEFAULT now(),
    publicado_en TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_outbox_evento_pendiente
    ON ms_polizas.outbox_evento (creado_en) WHERE publicado_en IS NULL;
