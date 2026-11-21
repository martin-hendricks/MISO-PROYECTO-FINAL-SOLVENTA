CREATE TABLE IF NOT EXISTS ms_identidad.socio (
    socio_id   UUID PRIMARY KEY,
    nombre     TEXT NOT NULL,
    alcances   JSONB NOT NULL,
    estado     TEXT NOT NULL,
    creado_en  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_socio_estado CHECK (estado IN ('activo', 'revocado'))
);

CREATE TABLE IF NOT EXISTS ms_identidad.credencial_socio (
    credencial_id  UUID PRIMARY KEY,
    socio_id       UUID NOT NULL REFERENCES ms_identidad.socio (socio_id),
    huella_sha256  TEXT NOT NULL,
    creada_en      TIMESTAMPTZ NOT NULL DEFAULT now(),
    revocada_en    TIMESTAMPTZ,
    CONSTRAINT uq_credencial_socio_huella UNIQUE (huella_sha256)
);

CREATE INDEX IF NOT EXISTS ix_credencial_socio_socio ON ms_identidad.credencial_socio (socio_id);
