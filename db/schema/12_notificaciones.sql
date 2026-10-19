-- notificaciones: notificaciones enviadas al usuario (consistencia eventual).
-- Requiere PostgreSQL 13+ (gen_random_uuid() nativo).

CREATE SCHEMA IF NOT EXISTS notificaciones;

CREATE TABLE notificaciones.notificacion (
    notificacion_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id        UUID        NOT NULL,
    evento_origen_id  UUID,
    canal             TEXT        NOT NULL,
    tipo              TEXT        NOT NULL,
    estado            TEXT        NOT NULL,
    enviada_en        TIMESTAMPTZ,
    -- Idempotencia del consumidor: un evento genera a lo sumo una notificación por canal (§1.1.4.4, EC-ESC-03).
    CONSTRAINT uq_notificacion_evento_canal UNIQUE (evento_origen_id, canal)
);

COMMENT ON COLUMN notificaciones.notificacion.evento_origen_id IS 'id del evento de dominio que originó la notificación; NULL si no proviene del bus';

COMMENT ON COLUMN notificaciones.notificacion.usuario_id IS 'ref lógica -> ms_identidad.usuario.usuario_id';

CREATE INDEX ix_notificacion_usuario ON notificaciones.notificacion (usuario_id);
