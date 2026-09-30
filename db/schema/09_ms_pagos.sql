-- ms_pagos: medios de pago, pagos (recaudo de prima / indemnización) y transacciones con pasarela.

CREATE TABLE ms_pagos.medio_pago (
    medio_pago_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id        UUID NOT NULL,
    tipo              TEXT NOT NULL,
    token_referencia  TEXT NOT NULL
);

COMMENT ON COLUMN ms_pagos.medio_pago.usuario_id IS 'ref lógica -> ms_identidad.usuario.usuario_id';

CREATE INDEX ix_medio_pago_usuario ON ms_pagos.medio_pago (usuario_id);

CREATE TABLE ms_pagos.pago (
    pago_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    medio_pago_id   UUID          NOT NULL REFERENCES ms_pagos.medio_pago(medio_pago_id),
    prima_id        UUID,
    reclamacion_id  UUID,
    monto           NUMERIC(14,2) NOT NULL,
    concepto        TEXT          NOT NULL,
    estado          TEXT          NOT NULL,
    fecha           TIMESTAMPTZ   NOT NULL DEFAULT now()
);

COMMENT ON COLUMN ms_pagos.pago.prima_id       IS 'ref lógica opcional -> ms_polizas.prima.prima_id';
COMMENT ON COLUMN ms_pagos.pago.reclamacion_id IS 'ref lógica opcional -> ms_siniestros.reclamacion.reclamacion_id';

CREATE INDEX ix_pago_medio_pago  ON ms_pagos.pago (medio_pago_id);
CREATE INDEX ix_pago_prima       ON ms_pagos.pago (prima_id)       WHERE prima_id IS NOT NULL;
CREATE INDEX ix_pago_reclamacion ON ms_pagos.pago (reclamacion_id) WHERE reclamacion_id IS NOT NULL;

CREATE TABLE ms_pagos.transaccion_pasarela (
    transaccion_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pago_id             UUID NOT NULL REFERENCES ms_pagos.pago(pago_id),
    proveedor           TEXT NOT NULL,
    referencia_externa  TEXT,
    estado              TEXT NOT NULL,
    idempotency_key     TEXT NOT NULL,
    CONSTRAINT uq_transaccion_idempotency UNIQUE (idempotency_key)
);

CREATE INDEX ix_transaccion_pago ON ms_pagos.transaccion_pasarela (pago_id);
