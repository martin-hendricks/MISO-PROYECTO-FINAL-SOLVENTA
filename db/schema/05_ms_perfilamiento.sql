-- ms_perfilamiento: perfil de riesgo y trazabilidad de fuentes consultadas.

CREATE TABLE ms_perfilamiento.perfil_riesgo (
    perfil_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id    UUID             NOT NULL,
    score         DOUBLE PRECISION NOT NULL,
    segmento      TEXT             NOT NULL,
    explicacion   TEXT,
    calculado_en  TIMESTAMPTZ      NOT NULL DEFAULT now()
);

COMMENT ON COLUMN ms_perfilamiento.perfil_riesgo.usuario_id IS 'ref lógica -> ms_identidad.usuario.usuario_id';

CREATE INDEX ix_perfil_usuario ON ms_perfilamiento.perfil_riesgo (usuario_id, calculado_en DESC);

CREATE TABLE ms_perfilamiento.fuente_dato_consultada (
    fuente_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    perfil_id    UUID        NOT NULL REFERENCES ms_perfilamiento.perfil_riesgo(perfil_id),
    proveedor    TEXT        NOT NULL,
    tipo_dato    TEXT        NOT NULL,
    resultado    TEXT        NOT NULL,
    "timestamp"  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_fuente_perfil ON ms_perfilamiento.fuente_dato_consultada (perfil_id);
