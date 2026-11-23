-- Moneda del aviso. La parametría sigue en COP; un aviso nuevo guarda la moneda
-- de la póliza (la de su cotización) y la reserva se expresa en esa moneda.
-- Los avisos ya guardados quedan en COP.

ALTER TABLE ms_siniestros.siniestro
    ADD COLUMN IF NOT EXISTS moneda TEXT NOT NULL DEFAULT 'COP';

ALTER TABLE ms_siniestros.siniestro
    DROP CONSTRAINT IF EXISTS ck_siniestro_moneda;

ALTER TABLE ms_siniestros.siniestro
    ADD CONSTRAINT ck_siniestro_moneda CHECK (moneda IN ('COP', 'MXN', 'CLP', 'PEN'));

COMMENT ON COLUMN ms_siniestros.siniestro.moneda IS
    'Moneda de la póliza al reportar el aviso. La reserva y el pago quedan en esta moneda.';
