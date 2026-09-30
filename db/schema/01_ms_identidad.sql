-- ms_identidad: usuarios y sesiones.

CREATE TABLE ms_identidad.usuario (
    usuario_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo_documento    TEXT NOT NULL,
    numero_documento  TEXT NOT NULL,
    email             TEXT NOT NULL,
    password_hash     TEXT NOT NULL,
    estado            TEXT NOT NULL,
    CONSTRAINT uq_usuario_documento UNIQUE (tipo_documento, numero_documento),
    CONSTRAINT uq_usuario_email     UNIQUE (email)
);

CREATE TABLE ms_identidad.sesion_token (
    token_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id  UUID        NOT NULL REFERENCES ms_identidad.usuario(usuario_id),
    tipo        TEXT        NOT NULL,
    emitido_en  TIMESTAMPTZ NOT NULL DEFAULT now(),
    expira_en   TIMESTAMPTZ NOT NULL
);

CREATE INDEX ix_sesion_token_usuario ON ms_identidad.sesion_token (usuario_id);
