-- ms-notificaciones: almacén propio de notificaciones y dispositivos push.
-- PostgreSQL 13+ (gen_random_uuid() nativo). Idempotente: se puede reaplicar.

CREATE SCHEMA IF NOT EXISTS notificaciones;

CREATE TABLE IF NOT EXISTS notificaciones.notificacion (
    notificacion_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id        UUID        NOT NULL,
    evento_origen_id  UUID,
    canal             TEXT        NOT NULL,
    tipo              TEXT        NOT NULL,
    titulo            TEXT        NOT NULL,
    cuerpo            TEXT        NOT NULL,
    destino           TEXT,
    estado            TEXT        NOT NULL,
    creada_en         TIMESTAMPTZ NOT NULL DEFAULT now(),
    enviada_en        TIMESTAMPTZ,
    leida_en          TIMESTAMPTZ,
    proveedor_id      TEXT,
    -- Idempotencia del consumidor: un evento genera a lo sumo una notificación por canal.
    CONSTRAINT uq_notificacion_evento_canal UNIQUE (evento_origen_id, canal)
);

-- El DDL canónico db/schema/12_notificaciones.sql puede haber creado antes la tabla
-- con un subconjunto de columnas (desarrollo local comparte una sola base de datos).
-- Estas sentencias son no-op sobre una tabla recién creada y completan la canónica.
ALTER TABLE notificaciones.notificacion
    ADD COLUMN IF NOT EXISTS titulo TEXT NOT NULL DEFAULT '';
ALTER TABLE notificaciones.notificacion
    ADD COLUMN IF NOT EXISTS cuerpo TEXT NOT NULL DEFAULT '';
ALTER TABLE notificaciones.notificacion
    ADD COLUMN IF NOT EXISTS destino TEXT;
ALTER TABLE notificaciones.notificacion
    ADD COLUMN IF NOT EXISTS creada_en TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE notificaciones.notificacion
    ADD COLUMN IF NOT EXISTS leida_en TIMESTAMPTZ;
ALTER TABLE notificaciones.notificacion
    ADD COLUMN IF NOT EXISTS proveedor_id TEXT;
ALTER TABLE notificaciones.notificacion ALTER COLUMN titulo DROP DEFAULT;
ALTER TABLE notificaciones.notificacion ALTER COLUMN cuerpo DROP DEFAULT;

CREATE TABLE IF NOT EXISTS notificaciones.dispositivo_push (
    dispositivo_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id     UUID        NOT NULL,
    plataforma     TEXT        NOT NULL,
    token          TEXT        NOT NULL,
    activo         BOOLEAN     NOT NULL DEFAULT true,
    creado_en      TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_dispositivo_usuario_token UNIQUE (usuario_id, token)
);

CREATE INDEX IF NOT EXISTS ix_notificacion_usuario
    ON notificaciones.notificacion (usuario_id, creada_en DESC);

-- Si el DDL canónico creó ix_notificacion_usuario solo por usuario_id, se reemplaza
-- por el índice compuesto que usa el listado paginado. En una base nueva es no-op.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE schemaname = 'notificaciones'
          AND indexname = 'ix_notificacion_usuario'
          AND indexdef LIKE '%creada_en%'
    ) THEN
        DROP INDEX IF EXISTS notificaciones.ix_notificacion_usuario;
        CREATE INDEX ix_notificacion_usuario
            ON notificaciones.notificacion (usuario_id, creada_en DESC);
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS ix_dispositivo_usuario
    ON notificaciones.dispositivo_push (usuario_id, activo);

COMMENT ON TABLE notificaciones.notificacion IS 'Notificaciones al usuario; el consumidor de MSK las crea de forma idempotente por (evento_origen_id, canal)';
COMMENT ON COLUMN notificaciones.notificacion.usuario_id IS 'ref lógica -> ms_identidad.usuario.usuario_id';
COMMENT ON COLUMN notificaciones.notificacion.evento_origen_id IS 'id del evento de dominio que originó la notificación; NULL si no proviene del bus';
COMMENT ON COLUMN notificaciones.notificacion.canal IS 'push | email';
COMMENT ON COLUMN notificaciones.notificacion.estado IS 'pendiente | enviada | fallida | leida';
COMMENT ON COLUMN notificaciones.notificacion.proveedor_id IS 'id devuelto por el proveedor de push al enviar';

COMMENT ON TABLE notificaciones.dispositivo_push IS 'Dispositivos push registrados por el cliente (token FCM/APNs)';
COMMENT ON COLUMN notificaciones.dispositivo_push.plataforma IS 'android | ios';
COMMENT ON COLUMN notificaciones.dispositivo_push.activo IS 'false cuando el cliente elimina el dispositivo; el registro se conserva para el upsert';
