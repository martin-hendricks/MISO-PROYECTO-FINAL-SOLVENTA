ALTER TABLE ms_identidad.usuario
    ADD COLUMN IF NOT EXISTS ingresos_mensuales NUMERIC(14, 2),
    ADD COLUMN IF NOT EXISTS gastos_mensuales NUMERIC(14, 2);

ALTER TABLE ms_identidad.usuario
    DROP CONSTRAINT IF EXISTS ck_usuario_ingresos_positivos;

ALTER TABLE ms_identidad.usuario
    ADD CONSTRAINT ck_usuario_ingresos_positivos
    CHECK (ingresos_mensuales IS NULL OR ingresos_mensuales > 0);

ALTER TABLE ms_identidad.usuario
    DROP CONSTRAINT IF EXISTS ck_usuario_gastos_no_negativos;

ALTER TABLE ms_identidad.usuario
    ADD CONSTRAINT ck_usuario_gastos_no_negativos
    CHECK (gastos_mensuales IS NULL OR gastos_mensuales >= 0);
