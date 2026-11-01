-- ms_suscripcion: regla aplicada en cada decisión (HU-149, SOLV-112).
-- Incremental sobre db/01_ms_suscripcion.sql. Guarda una copia de la regla
-- vigente al decidir, para que la decisión siga siendo auditable si la regla
-- cambia. Las decisiones anteriores quedan con NULL.

ALTER TABLE ms_suscripcion.suscripcion ADD COLUMN IF NOT EXISTS regla TEXT;
