-- Copia literal del DDL de apps/backend/ms-siniestros/db/07_pago_parametrico_comprobante.sql.
-- Comprobante estable del pago paramétrico, para la billetera del cliente.

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
