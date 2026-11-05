-- Póliza del siniestro paramétrico. Las bases creadas antes de esta columna
-- en el CREATE TABLE de 02_ms_siniestros_parametrico.sql no la recibieron:
-- esa migración ya estaba registrada y no vuelve a correr.

ALTER TABLE ms_siniestros.siniestro
    ADD COLUMN IF NOT EXISTS poliza_id UUID;

COMMENT ON COLUMN ms_siniestros.siniestro.poliza_id IS
    'ref lógica -> ms_polizas.poliza.poliza_id; NULL si el origen del evento no la conoce';

CREATE INDEX IF NOT EXISTS ix_siniestro_poliza
    ON ms_siniestros.siniestro (poliza_id)
    WHERE poliza_id IS NOT NULL;
