CREATE SCHEMA IF NOT EXISTS siniestros_w;

CREATE TABLE siniestros_w.poliza (
    id              BIGINT PRIMARY KEY,
    cliente_id      BIGINT        NOT NULL,
    numero          TEXT          NOT NULL,
    producto        TEXT          NOT NULL,
    estado          TEXT          NOT NULL,
    suma_asegurada  NUMERIC(14,2) NOT NULL,
    vigencia_desde  DATE          NOT NULL,
    vigencia_hasta  DATE          NOT NULL
);

CREATE TABLE siniestros_w.siniestro (
    id                BIGINT PRIMARY KEY,
    poliza_id         BIGINT      NOT NULL REFERENCES siniestros_w.poliza(id),
    cliente_id        BIGINT      NOT NULL,
    numero            TEXT        NOT NULL,
    estado            TEXT        NOT NULL,
    causa             TEXT        NOT NULL,
    monto_estimado    NUMERIC(14,2),
    monto_aprobado    NUMERIC(14,2),
    fecha_ocurrencia  TIMESTAMPTZ NOT NULL,
    fecha_aviso       TIMESTAMPTZ NOT NULL,
    actualizado_en    TIMESTAMPTZ NOT NULL DEFAULT now(),
    version           INTEGER     NOT NULL DEFAULT 1
);

CREATE TABLE siniestros_w.hito (
    id            BIGSERIAL PRIMARY KEY,
    siniestro_id  BIGINT      NOT NULL REFERENCES siniestros_w.siniestro(id),
    tipo          TEXT        NOT NULL,
    descripcion   TEXT        NOT NULL,
    actor         TEXT        NOT NULL,
    ocurrido_en   TIMESTAMPTZ NOT NULL
);

CREATE TABLE siniestros_w.documento (
    id            BIGSERIAL PRIMARY KEY,
    siniestro_id  BIGINT      NOT NULL REFERENCES siniestros_w.siniestro(id),
    tipo          TEXT        NOT NULL,
    estado        TEXT        NOT NULL,
    cargado_en    TIMESTAMPTZ NOT NULL
);

CREATE TABLE siniestros_w.peritaje (
    id            BIGSERIAL PRIMARY KEY,
    siniestro_id  BIGINT      NOT NULL REFERENCES siniestros_w.siniestro(id),
    perito        TEXT        NOT NULL,
    estado        TEXT        NOT NULL,
    resultado     TEXT,
    agendado_para TIMESTAMPTZ
);

CREATE INDEX idx_hito_siniestro      ON siniestros_w.hito(siniestro_id);
CREATE INDEX idx_documento_siniestro ON siniestros_w.documento(siniestro_id);
CREATE INDEX idx_peritaje_siniestro  ON siniestros_w.peritaje(siniestro_id);
