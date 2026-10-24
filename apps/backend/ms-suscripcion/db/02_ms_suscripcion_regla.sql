-- Regla de aceptación de riesgo como dato (HU-13, EC-MOD-04): cambiarla es un UPDATE,
-- no un despliegue. Un score <= score_maximo está dentro del apetito de riesgo.

CREATE TABLE IF NOT EXISTS ms_suscripcion.regla_suscripcion (
    regla_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    score_maximo       NUMERIC(10,4) NOT NULL CHECK (score_maximo >= 0),
    motivo_aceptacion  TEXT          NOT NULL,
    motivo_rechazo     TEXT          NOT NULL,
    vigente            BOOLEAN       NOT NULL DEFAULT true
);

-- Como máximo una regla vigente: la decisión es determinista.
CREATE UNIQUE INDEX IF NOT EXISTS uq_regla_suscripcion_vigente
    ON ms_suscripcion.regla_suscripcion (vigente) WHERE vigente;

INSERT INTO ms_suscripcion.regla_suscripcion (score_maximo, motivo_aceptacion, motivo_rechazo)
SELECT 0.7000, 'Riesgo dentro del apetito de la aseguradora', 'Riesgo fuera del apetito de la aseguradora'
WHERE NOT EXISTS (SELECT 1 FROM ms_suscripcion.regla_suscripcion WHERE vigente);
