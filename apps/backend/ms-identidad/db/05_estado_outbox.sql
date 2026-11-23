-- Outbox de ms-identidad para publicar cambios de estado de cuenta.
-- Misma forma que ms_polizas.outbox_evento para que outbox-relay la lea igual.

CREATE TABLE IF NOT EXISTS ms_identidad.outbox_evento (
    id           UUID PRIMARY KEY,
    tipo         TEXT        NOT NULL,
    agregado_id  UUID        NOT NULL,
    payload      JSONB       NOT NULL,
    creado_en    TIMESTAMPTZ NOT NULL DEFAULT now(),
    publicado_en TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_outbox_evento_pendiente
    ON ms_identidad.outbox_evento (creado_en)
    WHERE publicado_en IS NULL;
