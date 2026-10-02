-- analitica: eventos de dominio consumidos del bus (consistencia eventual).

CREATE TABLE analitica.evento_analitico (
    evento_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo_evento     TEXT        NOT NULL,
    entidad_origen  TEXT        NOT NULL,
    payload         JSONB       NOT NULL,
    "timestamp"     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_evento_analitico_tipo ON analitica.evento_analitico (tipo_evento, "timestamp");
