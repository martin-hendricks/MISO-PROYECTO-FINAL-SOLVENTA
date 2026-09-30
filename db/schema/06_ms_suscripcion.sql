-- ms_suscripcion: decisión de suscripción sobre una solicitud y un perfil.

CREATE TABLE ms_suscripcion.suscripcion (
    suscripcion_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    solicitud_id    UUID        NOT NULL,
    perfil_id       UUID        NOT NULL,
    decision        TEXT        NOT NULL,
    motivo          TEXT,
    evaluada_en     TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON COLUMN ms_suscripcion.suscripcion.solicitud_id IS 'ref lógica -> ms_cotizacion.solicitud_cotizacion.solicitud_id';
COMMENT ON COLUMN ms_suscripcion.suscripcion.perfil_id    IS 'ref lógica -> ms_perfilamiento.perfil_riesgo.perfil_id';

CREATE INDEX ix_suscripcion_solicitud ON ms_suscripcion.suscripcion (solicitud_id);
CREATE INDEX ix_suscripcion_perfil    ON ms_suscripcion.suscripcion (perfil_id);
