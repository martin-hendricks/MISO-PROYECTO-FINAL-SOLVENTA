-- Copia literal del DDL oficial: db/schema/01_ms_identidad.sql
-- No se edita aquí: cualquier cambio de dominio va en db/schema/01_ms_identidad.sql.
-- Requiere PostgreSQL 13+ (gen_random_uuid() nativo).

CREATE SCHEMA IF NOT EXISTS ms_identidad;

CREATE TABLE ms_identidad.usuario (
    usuario_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo_documento    TEXT NOT NULL,
    numero_documento  TEXT NOT NULL,
    email             TEXT NOT NULL,
    password_hash     TEXT NOT NULL,
    estado            TEXT NOT NULL,
    CONSTRAINT uq_usuario_documento UNIQUE (tipo_documento, numero_documento)
);

-- Unicidad de email sin distinguir mayúsculas/minúsculas.
CREATE UNIQUE INDEX uq_usuario_email ON ms_identidad.usuario (lower(email));

CREATE TABLE ms_identidad.sesion_token (
    token_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id  UUID        NOT NULL REFERENCES ms_identidad.usuario(usuario_id),
    tipo        TEXT        NOT NULL,
    emitido_en  TIMESTAMPTZ NOT NULL DEFAULT now(),
    expira_en   TIMESTAMPTZ NOT NULL
);

CREATE INDEX ix_sesion_token_usuario ON ms_identidad.sesion_token (usuario_id);
