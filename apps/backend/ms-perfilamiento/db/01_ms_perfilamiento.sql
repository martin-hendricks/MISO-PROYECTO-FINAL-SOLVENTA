CREATE SCHEMA IF NOT EXISTS ms_perfilamiento;

CREATE TABLE IF NOT EXISTS ms_perfilamiento.consentimiento (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id   TEXT NOT NULL,
    otorgado_en  TIMESTAMPTZ NOT NULL DEFAULT now(),
    revocado_en  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_consentimiento_cliente_id
    ON ms_perfilamiento.consentimiento (cliente_id);

-- A lo sumo un consentimiento VIGENTE (no revocado) por cliente: otorgar es idempotente
-- mientras no se revoque (HU-53).
CREATE UNIQUE INDEX IF NOT EXISTS uq_consentimiento_vigente_por_cliente
    ON ms_perfilamiento.consentimiento (cliente_id) WHERE revocado_en IS NULL;

CREATE TABLE IF NOT EXISTS ms_perfilamiento.oferta (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idempotency_key     TEXT NOT NULL,
    cliente_id          TEXT NOT NULL,
    precio              NUMERIC(14,2) NOT NULL CHECK (precio > 0),
    moneda              TEXT NOT NULL,
    degradado           BOOLEAN NOT NULL DEFAULT false,
    factores            JSONB NOT NULL,
    snapshot_atributos  JSONB NOT NULL,
    creado_en           TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_oferta_idempotency_key UNIQUE (idempotency_key)
);

CREATE INDEX IF NOT EXISTS ix_oferta_cliente_id
    ON ms_perfilamiento.oferta (cliente_id);

CREATE TABLE IF NOT EXISTS ms_perfilamiento.outbox_evento (
    id           UUID PRIMARY KEY,
    tipo         TEXT NOT NULL,
    agregado_id  UUID NOT NULL,
    payload      JSONB NOT NULL,
    creado_en    TIMESTAMPTZ NOT NULL DEFAULT now(),
    publicado_en TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_outbox_evento_pendiente
    ON ms_perfilamiento.outbox_evento (creado_en) WHERE publicado_en IS NULL;
