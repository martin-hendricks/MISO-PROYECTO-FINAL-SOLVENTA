CREATE SCHEMA IF NOT EXISTS ms_consentimiento;

-- STUB de consentimiento de habeas data (Ley 1581 colombiana). Registra
-- únicamente el hecho de otorgamiento/revocación con su marca de tiempo.
-- No versiona política/texto legal (no hay version_politica ni snapshot
-- del documento aceptado) y no tiene outbox: la revocación NO se propaga
-- por eventos a otros microservicios (ver app/domain/modelos.py para el
-- detalle de qué cubre y qué no cubre este servicio).
CREATE TABLE IF NOT EXISTS ms_consentimiento.consentimiento (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id   TEXT NOT NULL,
    otorgado_en  TIMESTAMPTZ NOT NULL DEFAULT now(),
    revocado_en  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_consentimiento_cliente_id
    ON ms_consentimiento.consentimiento (cliente_id);

-- A lo sumo un consentimiento VIGENTE (no revocado) por cliente: otorgar es
-- idempotente mientras no se revoque.
CREATE UNIQUE INDEX IF NOT EXISTS uq_consentimiento_vigente_por_cliente
    ON ms_consentimiento.consentimiento (cliente_id) WHERE revocado_en IS NULL;
