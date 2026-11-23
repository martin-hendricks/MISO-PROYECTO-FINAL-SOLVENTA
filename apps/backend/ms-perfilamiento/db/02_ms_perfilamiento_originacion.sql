CREATE TABLE IF NOT EXISTS ms_perfilamiento.originacion (
    id           UUID PRIMARY KEY,
    cliente_id   TEXT NOT NULL,
    valor        NUMERIC(16,2) NOT NULL CHECK (valor > 0),
    plazo_meses  INTEGER NOT NULL CHECK (plazo_meses BETWEEN 1 AND 480),
    origen       TEXT NOT NULL CHECK (origen IN ('cliente', 'socio')),
    creada_en    TIMESTAMPTZ NOT NULL DEFAULT now(),
    cerrada_en   TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_originacion_cliente_id
    ON ms_perfilamiento.originacion (cliente_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_originacion_pendiente_por_cliente
    ON ms_perfilamiento.originacion (cliente_id) WHERE cerrada_en IS NULL;
