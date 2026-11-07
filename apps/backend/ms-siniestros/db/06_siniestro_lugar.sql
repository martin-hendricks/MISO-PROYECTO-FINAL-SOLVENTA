-- Lugar del hecho en el aviso asistido. Las bases que ya aplicaron
-- 05_ms_siniestros_aviso_asistido.sql no recibieron la columna: esa
-- migración ya está registrada y no vuelve a correr.

ALTER TABLE ms_siniestros.siniestro
    ADD COLUMN IF NOT EXISTS lugar TEXT;

COMMENT ON COLUMN ms_siniestros.siniestro.lugar IS
    'Lugar del hecho declarado por el cliente; NULL si no lo indicó';
