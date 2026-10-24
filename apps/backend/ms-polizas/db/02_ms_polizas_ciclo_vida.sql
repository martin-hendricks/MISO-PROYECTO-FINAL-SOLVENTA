-- ms_polizas: ciclo de vida (HU-59 renovar, HU-60 modificar, HU-61 cancelar).
-- Incremental sobre db/01_ms_polizas.sql: agrega los campos de auditoría de
-- cancelación y el estado CANCELADA al dominio de valores de poliza.estado.

ALTER TABLE ms_polizas.poliza
    ADD COLUMN IF NOT EXISTS motivo_cancelacion TEXT,
    ADD COLUMN IF NOT EXISTS cancelada_en       DATE;

-- Auditable: si quedó cancelada, debe quedar registrado el motivo y la fecha.
ALTER TABLE ms_polizas.poliza
    DROP CONSTRAINT IF EXISTS ck_poliza_cancelacion;
ALTER TABLE ms_polizas.poliza
    ADD CONSTRAINT ck_poliza_cancelacion CHECK (
        estado <> 'CANCELADA' OR (motivo_cancelacion IS NOT NULL AND cancelada_en IS NOT NULL)
    );

COMMENT ON COLUMN ms_polizas.poliza.motivo_cancelacion IS 'Motivo de la cancelación (HU-61); NULL mientras la póliza esté vigente';
COMMENT ON COLUMN ms_polizas.poliza.cancelada_en       IS 'Fecha en la que se canceló la póliza (HU-61); NULL mientras esté vigente';
