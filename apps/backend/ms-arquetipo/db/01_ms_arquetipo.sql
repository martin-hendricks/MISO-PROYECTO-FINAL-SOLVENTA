CREATE SCHEMA IF NOT EXISTS ms_arquetipo;

CREATE TABLE IF NOT EXISTS ms_arquetipo.ejemplo (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idempotency_key TEXT NOT NULL,
    referencia      TEXT NOT NULL,
    monto           NUMERIC(14,2) NOT NULL CHECK (monto > 0),
    estado          TEXT NOT NULL,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_ejemplo_idempotency_key UNIQUE (idempotency_key)
);

CREATE TABLE IF NOT EXISTS ms_arquetipo.outbox_evento (
    id           UUID PRIMARY KEY,
    tipo         TEXT NOT NULL,
    agregado_id  UUID NOT NULL,
    payload      JSONB NOT NULL,
    creado_en    TIMESTAMPTZ NOT NULL DEFAULT now(),
    publicado_en TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_outbox_evento_pendiente
    ON ms_arquetipo.outbox_evento (creado_en) WHERE publicado_en IS NULL;
