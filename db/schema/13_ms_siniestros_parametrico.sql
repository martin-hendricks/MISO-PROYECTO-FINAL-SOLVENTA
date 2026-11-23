-- ms_siniestros: extensión aditiva del DDL oficial db/schema/08_ms_siniestros.sql.
-- Cubre HU-30/32/33/34 (SOLV-123/125/126/127): máquina de estados única del siniestro,
-- ingesta idempotente del evento paramétrico simulado, evaluación determinista del
-- umbral y pago paramétrico stub. No agrega tablas nuevas al esquema de reclamación
-- manual (reclamacion/evidencia_siniestro/evaluacion_siniestro); el agregado Siniestro
-- de estas HU es independiente y reutilizable por los flujos futuros.
-- Requiere PostgreSQL 13+ (gen_random_uuid() nativo).

CREATE TABLE ms_siniestros.siniestro (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evento_id   TEXT        NOT NULL,
    estado      TEXT        NOT NULL,
    creado_en   TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- HU-61 (back-office): liga el siniestro a la póliza cuando el origen del
    -- evento la conoce, para que ms-polizas/bff-web puedan consultar
    -- siniestros abiertos antes de cancelar (GET /v1/siniestros/abiertos).
    -- NULL para eventos cuyo origen no la conoce (stub de ingesta).
    poliza_id   UUID,
    CONSTRAINT uq_siniestro_evento_id UNIQUE (evento_id)
);

COMMENT ON COLUMN ms_siniestros.siniestro.poliza_id IS 'ref lógica -> ms_polizas.poliza.poliza_id; NULL si el origen del evento no la conoce';

CREATE INDEX ix_siniestro_poliza ON ms_siniestros.siniestro (poliza_id) WHERE poliza_id IS NOT NULL;

-- Modelo único de estados (HU-30): recibido, en_evaluacion, decidido, enrutado, pagado.
-- Todos los canales (cola del operador, decisión, pago, lista del cliente) leen de aquí.
CREATE TABLE ms_siniestros.siniestro_transicion (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    siniestro_id  UUID        NOT NULL REFERENCES ms_siniestros.siniestro(id),
    estado        TEXT        NOT NULL,
    ocurrido_en   TIMESTAMPTZ NOT NULL DEFAULT now(),
    origen        TEXT        NOT NULL
);

CREATE INDEX ix_siniestro_transicion_siniestro ON ms_siniestros.siniestro_transicion (siniestro_id);

-- Evento simulado (HU-32): id + un único valor comparable. evento_id es la clave de
-- idempotencia: reingestar el mismo id no dispara una segunda evaluación.
CREATE TABLE ms_siniestros.evento_parametrico (
    evento_id     TEXT          PRIMARY KEY,
    valor         NUMERIC(18,4) NOT NULL,
    recibido_en   TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- Resultado persistido de la evaluación de umbral (HU-33). El umbral y la vigencia de
-- la póliza viajan en la solicitud de evaluación (parámetro); este servicio NO integra
-- por red con ms-polizas en este alcance (ver README del servicio).
CREATE TABLE ms_siniestros.evaluacion_umbral (
    id              UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    evento_id       TEXT          NOT NULL REFERENCES ms_siniestros.evento_parametrico(evento_id),
    umbral          NUMERIC(18,4) NOT NULL,
    valor           NUMERIC(18,4) NOT NULL,
    poliza_vigente  BOOLEAN       NOT NULL,
    decision        BOOLEAN       NOT NULL,
    motivo          TEXT          NOT NULL,
    evaluada_en     TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CONSTRAINT uq_evaluacion_umbral_evento UNIQUE (evento_id)
);

-- Pago paramétrico stub (HU-34): desembolso simulado, idempotente por evento_id.
CREATE TABLE ms_siniestros.pago_parametrico (
    id            UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    evento_id     TEXT          NOT NULL REFERENCES ms_siniestros.evento_parametrico(evento_id),
    siniestro_id  UUID          NOT NULL REFERENCES ms_siniestros.siniestro(id),
    monto         NUMERIC(14,2) NOT NULL CHECK (monto > 0),
    pagado_en     TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CONSTRAINT uq_pago_parametrico_evento UNIQUE (evento_id)
);

CREATE INDEX ix_pago_parametrico_siniestro ON ms_siniestros.pago_parametrico (siniestro_id);

-- Infraestructura técnica del patrón transactional outbox (no es DDL de dominio, mismo
-- patrón que ms-arquetipo / ms-cotizacion).
CREATE TABLE ms_siniestros.outbox_evento (
    id           UUID PRIMARY KEY,
    tipo         TEXT NOT NULL,
    agregado_id  UUID NOT NULL,
    payload      JSONB NOT NULL,
    creado_en    TIMESTAMPTZ NOT NULL DEFAULT now(),
    publicado_en TIMESTAMPTZ
);

CREATE INDEX ix_outbox_evento_pendiente
    ON ms_siniestros.outbox_evento (creado_en) WHERE publicado_en IS NULL;
