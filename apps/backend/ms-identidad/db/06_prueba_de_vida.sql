-- Resultado simulado de la prueba de vida. La foto no se guarda.
-- ok o no. Las cuentas que ya existen quedan en no.

ALTER TABLE ms_identidad.usuario
    ADD COLUMN IF NOT EXISTS prueba_de_vida TEXT NOT NULL DEFAULT 'no'
        CHECK (prueba_de_vida IN ('ok', 'no'));
