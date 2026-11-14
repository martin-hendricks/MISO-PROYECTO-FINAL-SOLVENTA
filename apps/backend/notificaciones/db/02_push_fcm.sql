-- Push FCM: número de póliza, difusiones del operador y consumo idempotente de eventos
-- que no crean una fila de notificación. Reaplicable.

ALTER TABLE notificaciones.notificacion
    ADD COLUMN IF NOT EXISTS poliza TEXT;

ALTER TABLE notificaciones.notificacion
    ADD COLUMN IF NOT EXISTS difusion_id UUID;

COMMENT ON COLUMN notificaciones.notificacion.poliza IS 'ref lógica -> ms_polizas.poliza.numero';

CREATE TABLE IF NOT EXISTS notificaciones.difusion (
    difusion_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    autor_id        UUID        NOT NULL,
    titulo          TEXT        NOT NULL,
    cuerpo          TEXT        NOT NULL,
    poliza          TEXT,
    audiencia       TEXT        NOT NULL,
    destinatarios   INTEGER     NOT NULL,
    enviadas        INTEGER     NOT NULL DEFAULT 0,
    fallidas        INTEGER     NOT NULL DEFAULT 0,
    sin_dispositivo INTEGER     NOT NULL DEFAULT 0,
    creada_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_difusion_audiencia CHECK (audiencia IN ('todos', 'usuarios'))
);

COMMENT ON COLUMN notificaciones.difusion.autor_id IS 'ref lógica -> ms_identidad.usuario.usuario_id';
COMMENT ON COLUMN notificaciones.difusion.poliza IS 'ref lógica -> ms_polizas.poliza.numero';

ALTER TABLE notificaciones.notificacion
    DROP CONSTRAINT IF EXISTS fk_notificacion_difusion;
ALTER TABLE notificaciones.notificacion
    ADD CONSTRAINT fk_notificacion_difusion
    FOREIGN KEY (difusion_id) REFERENCES notificaciones.difusion (difusion_id);

CREATE INDEX IF NOT EXISTS ix_notificacion_difusion
    ON notificaciones.notificacion (difusion_id);

CREATE INDEX IF NOT EXISTS ix_difusion_creada
    ON notificaciones.difusion (creada_en DESC);

CREATE TABLE IF NOT EXISTS notificaciones.evento_consumido (
    evento_id    UUID PRIMARY KEY,
    tipo         TEXT        NOT NULL,
    procesado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
