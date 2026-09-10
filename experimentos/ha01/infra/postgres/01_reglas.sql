-- Conjunto de reglas de tarifa. Se carga UNA VEZ al arranque de la API.
-- PostgreSQL no participa del camino critico a proposito: la unica variable
-- bajo estudio debe ser la resolucion del perfil de Open Finance.

CREATE TABLE reglas_tarifa (
    producto                TEXT PRIMARY KEY,
    prima_base              NUMERIC(12, 2) NOT NULL,
    -- Recargo aplicado cuando la cotizacion se resuelve con valor de
    -- respaldo o por defecto. Su valor es una decision actuarial; su
    -- existencia hace visible que la degradacion elegante tiene un precio
    -- de negocio y no solo un beneficio de latencia.
    recargo_incertidumbre   NUMERIC(4, 3) NOT NULL,
    vigente_desde           DATE NOT NULL DEFAULT CURRENT_DATE
);

INSERT INTO reglas_tarifa (producto, prima_base, recargo_incertidumbre) VALUES
    ('VIAJE_BASICO',    120000.00, 1.150),
    ('VIAJE_PLUS',      185000.00, 1.180),
    ('DISPOSITIVO',      64000.00, 1.120),
    ('ACCIDENTES',       98000.00, 1.140);
