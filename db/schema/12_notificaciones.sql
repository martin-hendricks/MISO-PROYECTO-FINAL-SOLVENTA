-- notificaciones: notificaciones enviadas al usuario (consistencia eventual).

CREATE TABLE notificaciones.notificacion (
    notificacion_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id       UUID        NOT NULL,
    canal            TEXT        NOT NULL,
    tipo             TEXT        NOT NULL,
    estado           TEXT        NOT NULL,
    enviada_en       TIMESTAMPTZ
);

COMMENT ON COLUMN notificaciones.notificacion.usuario_id IS 'ref lógica -> ms_identidad.usuario.usuario_id';

CREATE INDEX ix_notificacion_usuario ON notificaciones.notificacion (usuario_id);
