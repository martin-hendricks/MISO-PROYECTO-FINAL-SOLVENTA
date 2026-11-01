-- ms_perfilamiento: consentimiento de perfilamiento (HU-53, distinto e independiente
-- del consentimiento general de datos en ms_consentimiento), adaptadores stub de Open
-- Finance/Open Data (HU-54), perfil y oferta explicable con degradación (HU-55/HU-56).
-- Requiere PostgreSQL 13+ (gen_random_uuid() nativo).

CREATE SCHEMA IF NOT EXISTS ms_perfilamiento;

CREATE TABLE ms_perfilamiento.consentimiento (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id   TEXT NOT NULL,
    otorgado_en  TIMESTAMPTZ NOT NULL DEFAULT now(),
    revocado_en  TIMESTAMPTZ
);

COMMENT ON TABLE ms_perfilamiento.consentimiento IS
    'Consentimiento de PERFILAMIENTO (HU-53): se otorga y revoca por separado de
     ms_consentimiento.consentimiento_datos (consentimiento general de uso de datos,
     otra HU). Sin fila vigente aquí, HU-54 no invoca ningún adaptador.';

CREATE INDEX ix_consentimiento_cliente_id ON ms_perfilamiento.consentimiento (cliente_id);

-- A lo sumo un consentimiento VIGENTE (no revocado) por cliente: otorgar es idempotente
-- mientras no se revoque.
CREATE UNIQUE INDEX uq_consentimiento_vigente_por_cliente
    ON ms_perfilamiento.consentimiento (cliente_id) WHERE revocado_en IS NULL;

CREATE TABLE ms_perfilamiento.oferta (
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

COMMENT ON COLUMN ms_perfilamiento.oferta.factores IS
    'Factores internos en lenguaje de negocio (HU-55): [{"factor","impacto","peso"}, ...]. Nunca el detalle crudo del proveedor.';
COMMENT ON COLUMN ms_perfilamiento.oferta.snapshot_atributos IS
    'Snapshot de los atributos de cada adaptador (o su valor de respaldo si degradado, HU-56) usados para esta oferta, para reconstruir la decisión al 100% aunque las reglas cambien después.';
COMMENT ON COLUMN ms_perfilamiento.oferta.degradado IS
    'true si al menos un adaptador (Open Finance u Open Data) excedió su timeout o falló y se usó valor de respaldo (HU-56). La oferta sigue siendo válida.';

CREATE INDEX ix_oferta_cliente_id ON ms_perfilamiento.oferta (cliente_id);

CREATE TABLE ms_perfilamiento.outbox_evento (
    id           UUID PRIMARY KEY,
    tipo         TEXT NOT NULL,
    agregado_id  UUID NOT NULL,
    payload      JSONB NOT NULL,
    creado_en    TIMESTAMPTZ NOT NULL DEFAULT now(),
    publicado_en TIMESTAMPTZ
);

CREATE INDEX ix_outbox_evento_pendiente
    ON ms_perfilamiento.outbox_evento (creado_en) WHERE publicado_en IS NULL;
