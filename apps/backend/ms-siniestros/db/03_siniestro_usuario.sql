-- Dueño del siniestro paramétrico. NULL en filas anteriores a esta columna.

ALTER TABLE ms_siniestros.siniestro
    ADD COLUMN IF NOT EXISTS usuario_id UUID;

CREATE INDEX IF NOT EXISTS ix_siniestro_usuario
    ON ms_siniestros.siniestro (usuario_id)
    WHERE usuario_id IS NOT NULL;
