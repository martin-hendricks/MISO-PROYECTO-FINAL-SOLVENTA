ALTER TABLE ms_polizas.poliza
    ADD COLUMN IF NOT EXISTS renovacion_automatica BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS renovacion_actualizada_en TIMESTAMPTZ;
