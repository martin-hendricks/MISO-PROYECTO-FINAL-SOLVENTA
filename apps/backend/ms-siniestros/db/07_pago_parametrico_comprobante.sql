-- Comprobante estable del pago paramétrico (billetera del cliente).
-- Reejecutable: la columna, el relleno y la unicidad se aplican solo si faltan.

ALTER TABLE ms_siniestros.pago_parametrico
    ADD COLUMN IF NOT EXISTS comprobante TEXT;

UPDATE ms_siniestros.pago_parametrico
SET comprobante = 'CMP-' || upper(left(replace(id::text, '-', ''), 10))
WHERE comprobante IS NULL;

ALTER TABLE ms_siniestros.pago_parametrico
    ALTER COLUMN comprobante SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_pago_parametrico_comprobante'
    ) THEN
        ALTER TABLE ms_siniestros.pago_parametrico
            ADD CONSTRAINT uq_pago_parametrico_comprobante UNIQUE (comprobante);
    END IF;
END $$;
