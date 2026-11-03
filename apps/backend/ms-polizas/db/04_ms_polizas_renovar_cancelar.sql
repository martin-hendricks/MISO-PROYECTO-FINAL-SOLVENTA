-- ms_polizas: datos de ciclo de vida para renovar y cancelar en back-office
-- (HU-59 ventana de gracia/prima, HU-61 auditoría de quién cancela y
-- devolución estimada). Incremental sobre db/01_ms_polizas.sql y
-- db/02_ms_polizas_ciclo_vida.sql.
--
-- La tabla ms_polizas.prima ya existía en 01_ms_polizas.sql pero nunca se
-- conectó al dominio/ORM -- esta migración no la toca, solo agrega lo que
-- faltaba en ms_polizas.poliza.

ALTER TABLE ms_polizas.poliza
    ADD COLUMN IF NOT EXISTS cancelada_por       TEXT,
    ADD COLUMN IF NOT EXISTS devolucion_estimada NUMERIC(14,2);

COMMENT ON COLUMN ms_polizas.poliza.cancelada_por       IS 'Identidad del operador que canceló (HU-61); NULL mientras esté vigente';
COMMENT ON COLUMN ms_polizas.poliza.devolucion_estimada IS 'Prorrata estimada de la prima al cancelar (HU-61); NULL mientras esté vigente';
