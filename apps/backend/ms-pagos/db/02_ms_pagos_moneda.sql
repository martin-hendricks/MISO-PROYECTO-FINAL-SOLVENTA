-- Moneda en la que empezó el cobro de la prima. Los cobros anteriores quedan en COP.
ALTER TABLE ms_pagos.pago
    ADD COLUMN IF NOT EXISTS moneda TEXT NOT NULL DEFAULT 'COP';

ALTER TABLE ms_pagos.pago
    DROP CONSTRAINT IF EXISTS ck_pago_moneda;

ALTER TABLE ms_pagos.pago
    ADD CONSTRAINT ck_pago_moneda CHECK (moneda ~ '^[A-Z]{3}$');
