-- Perfil compartido de la cuenta. Las columnas se agregan sobre el alta
-- existente; un volumen local viejo se recrea, no se migran identidades sintéticas.

ALTER TABLE ms_identidad.usuario
    ADD COLUMN IF NOT EXISTS nombre TEXT NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS apellidos TEXT NOT NULL DEFAULT '';
