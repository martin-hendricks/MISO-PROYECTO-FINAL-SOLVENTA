-- ms_siniestros: reclamaciones, evidencias y evaluación.

CREATE TABLE ms_siniestros.reclamacion (
    reclamacion_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    poliza_id        UUID          NOT NULL,
    usuario_id       UUID          NOT NULL,
    tipo             TEXT          NOT NULL,
    estado           TEXT          NOT NULL,
    monto_reclamado  NUMERIC(14,2) NOT NULL,
    reportada_en     TIMESTAMPTZ   NOT NULL DEFAULT now()
);

COMMENT ON COLUMN ms_siniestros.reclamacion.poliza_id  IS 'ref lógica -> ms_polizas.poliza.poliza_id';
COMMENT ON COLUMN ms_siniestros.reclamacion.usuario_id IS 'ref lógica -> ms_identidad.usuario.usuario_id';

CREATE INDEX ix_reclamacion_poliza  ON ms_siniestros.reclamacion (poliza_id);
CREATE INDEX ix_reclamacion_usuario ON ms_siniestros.reclamacion (usuario_id);

CREATE TABLE ms_siniestros.evidencia_siniestro (
    evidencia_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reclamacion_id  UUID        NOT NULL REFERENCES ms_siniestros.reclamacion(reclamacion_id),
    tipo_archivo    TEXT        NOT NULL,
    url             TEXT        NOT NULL,
    capturada_en    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_evidencia_reclamacion ON ms_siniestros.evidencia_siniestro (reclamacion_id);

CREATE TABLE ms_siniestros.evaluacion_siniestro (
    evaluacion_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reclamacion_id  UUID        NOT NULL REFERENCES ms_siniestros.reclamacion(reclamacion_id),
    resultado       TEXT        NOT NULL,
    observaciones   TEXT,
    evaluada_en     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_evaluacion_reclamacion ON ms_siniestros.evaluacion_siniestro (reclamacion_id);
