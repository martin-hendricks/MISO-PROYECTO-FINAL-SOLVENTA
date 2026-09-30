-- ms_polizas: póliza, coberturas y prima.

CREATE TABLE ms_polizas.poliza (
    poliza_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    oferta_id        UUID NOT NULL,
    usuario_id       UUID NOT NULL,
    numero           TEXT NOT NULL,
    inicio_vigencia  DATE NOT NULL,
    fin_vigencia     DATE NOT NULL,
    estado           TEXT NOT NULL,
    CONSTRAINT uq_poliza_numero   UNIQUE (numero),
    CONSTRAINT ck_poliza_vigencia CHECK (fin_vigencia >= inicio_vigencia)
);

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
