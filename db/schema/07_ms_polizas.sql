-- ms_polizas: póliza, coberturas y prima.
-- Requiere PostgreSQL 13+ (gen_random_uuid() nativo).

CREATE SCHEMA IF NOT EXISTS ms_polizas;

CREATE TABLE ms_polizas.poliza (
    poliza_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    oferta_id        UUID NOT NULL,
    usuario_id       UUID NOT NULL,
    numero           TEXT NOT NULL,
    inicio_vigencia  DATE NOT NULL,
    fin_vigencia     DATE NOT NULL,
    estado           TEXT NOT NULL,
    firma_hash       TEXT,
    CONSTRAINT uq_poliza_numero   UNIQUE (numero),
    CONSTRAINT ck_poliza_vigencia CHECK (fin_vigencia >= inicio_vigencia),
    -- Una póliza EMITIDA siempre lleva su hash de firma legal (VC-007).
    CONSTRAINT ck_poliza_firma    CHECK (estado <> 'EMITIDA' OR firma_hash IS NOT NULL)
);

COMMENT ON COLUMN ms_polizas.poliza.firma_hash IS 'FirmaHash de la póliza; se devuelve como HashFirmaLegal en PolizaEmitidaDTO (VC-007)';

COMMENT ON COLUMN ms_polizas.poliza.oferta_id  IS 'ref lógica -> ms_cotizacion.oferta_seguro.oferta_id';
COMMENT ON COLUMN ms_polizas.poliza.usuario_id IS 'ref lógica -> ms_identidad.usuario.usuario_id';

CREATE INDEX ix_poliza_oferta  ON ms_polizas.poliza (oferta_id);
CREATE INDEX ix_poliza_usuario ON ms_polizas.poliza (usuario_id);

CREATE TABLE ms_polizas.cobertura (
    cobertura_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    poliza_id       UUID          NOT NULL REFERENCES ms_polizas.poliza(poliza_id),
    nombre          TEXT          NOT NULL,
    suma_asegurada  NUMERIC(14,2) NOT NULL,
    deducible       NUMERIC(14,2) NOT NULL DEFAULT 0
);

CREATE INDEX ix_cobertura_poliza ON ms_polizas.cobertura (poliza_id);

CREATE TABLE ms_polizas.prima (
    prima_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    poliza_id      UUID          NOT NULL REFERENCES ms_polizas.poliza(poliza_id),
    valor          NUMERIC(14,2) NOT NULL,
    periodicidad   TEXT          NOT NULL,
    proximo_cobro  DATE
);

CREATE INDEX ix_prima_poliza ON ms_polizas.prima (poliza_id);

-- Outbox transaccional: el evento se inserta en la misma transacción que la póliza
-- y un relay lo publica en Kafka después del commit (PolizaEmitidaEvent, VC-007).
-- Si el servicio cae entre el commit y la publicación, el relay lo reintenta.
-- Tabla técnica, no es entidad del dominio (VC-004).
CREATE TABLE ms_polizas.outbox_evento (
    outbox_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agregado_tipo  TEXT        NOT NULL,
    agregado_id    UUID        NOT NULL,
    tipo_evento    TEXT        NOT NULL,
    payload        JSONB       NOT NULL,
    creado_en      TIMESTAMPTZ NOT NULL DEFAULT now(),
    publicado_en   TIMESTAMPTZ
);

COMMENT ON COLUMN ms_polizas.outbox_evento.outbox_id IS 'id del evento publicado; los consumidores lo guardan como evento_origen_id para deduplicar';

CREATE INDEX ix_outbox_pendiente ON ms_polizas.outbox_evento (creado_en) WHERE publicado_en IS NULL;
