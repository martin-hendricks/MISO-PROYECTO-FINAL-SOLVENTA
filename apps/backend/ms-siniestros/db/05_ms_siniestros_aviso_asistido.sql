-- Copia literal del DDL oficial: db/schema/14_ms_siniestros_aviso_asistido.sql
-- No se edita aquí: cualquier cambio de dominio va en db/schema/14_ms_siniestros_aviso_asistido.sql.
-- ms_siniestros: extensión aditiva para el siniestro asistido (HU-157, SOLV-256).
-- Cubre el alta del aviso en el núcleo (N5), la evidencia en S3 (N6), la parametría por
-- ramo que calcula la reserva y decide la aprobación automática, la retención por el
-- motor antifraude con traza (N15, EC-SEG-08), la decisión del operador con auditoría
-- (HU-27), el enrutamiento a perito (HU-28) y el pago de bajo monto idempotente (HU-29).
--
-- El siniestro asistido extiende el MISMO agregado `siniestro` de HU-30 (modelo único de
-- estados); no usa las tablas `reclamacion`/`evidencia_siniestro`/`evaluacion_siniestro`
-- del DDL 08, que quedan sin uso.
-- Requiere PostgreSQL 13+ y haber aplicado 08 y 13.

-- Número visible del aviso (SIN-1001, SIN-1002...), también para los paramétricos.
CREATE SEQUENCE ms_siniestros.siniestro_numero_seq START WITH 1001;

ALTER TABLE ms_siniestros.siniestro
    ALTER COLUMN evento_id DROP NOT NULL,
    ADD COLUMN numero                 TEXT          NOT NULL DEFAULT ('SIN-' || nextval('ms_siniestros.siniestro_numero_seq')),
    ADD COLUMN tipo                   TEXT          NOT NULL DEFAULT 'parametrico',
    -- IF NOT EXISTS: ms-siniestros/db/03_siniestro_usuario.sql ya la agrega para el paramétrico.
    ADD COLUMN IF NOT EXISTS usuario_id UUID,
    ADD COLUMN canal                  TEXT,
    ADD COLUMN ramo                   TEXT,
    ADD COLUMN poliza_numero          TEXT,
    ADD COLUMN poliza_estado          TEXT,
    ADD COLUMN poliza_inicio_vigencia DATE,
    ADD COLUMN poliza_fin_vigencia    DATE,
    ADD COLUMN suma_asegurada         NUMERIC(14,2),
    ADD COLUMN fecha_hecho            DATE,
    ADD COLUMN descripcion            TEXT,
    ADD COLUMN lugar                  TEXT,
    ADD COLUMN reserva                NUMERIC(14,2),
    ADD COLUMN umbral_automatico      NUMERIC(14,2),
    ADD COLUMN geo_lat                NUMERIC(9,6),
    ADD COLUMN geo_lng                NUMERIC(9,6),
    ADD COLUMN geo_precision_m        NUMERIC(10,2),
    ADD COLUMN resultado              TEXT,
    ADD COLUMN requiere_revision      BOOLEAN       NOT NULL DEFAULT false,
    ADD COLUMN motivo_revision        TEXT,
    ADD COLUMN clave_idempotencia     TEXT,
    ADD CONSTRAINT uq_siniestro_numero UNIQUE (numero),
    ADD CONSTRAINT uq_siniestro_clave_idempotencia UNIQUE (clave_idempotencia),
    ADD CONSTRAINT ck_siniestro_tipo CHECK (tipo IN ('parametrico', 'asistido')),
    ADD CONSTRAINT ck_siniestro_resultado CHECK (resultado IS NULL OR resultado IN ('aprobado', 'rechazado')),
    -- Un aviso asistido siempre sabe quién lo reporta, sobre qué póliza y cuándo ocurrió.
    ADD CONSTRAINT ck_siniestro_asistido_completo CHECK (
        tipo <> 'asistido' OR (usuario_id IS NOT NULL AND poliza_id IS NOT NULL AND fecha_hecho IS NOT NULL)
    );

COMMENT ON COLUMN ms_siniestros.siniestro.usuario_id IS 'ref lógica -> ms_identidad.usuario.usuario_id';
COMMENT ON COLUMN ms_siniestros.siniestro.ramo IS 'código de producto del catálogo de ms_cotizacion (p. ej. proteccion-dispositivo)';
COMMENT ON COLUMN ms_siniestros.siniestro.lugar IS 'Lugar del hecho declarado por el cliente; NULL si no lo indicó';
COMMENT ON COLUMN ms_siniestros.siniestro.reserva IS 'reserva calculada por la parametría del ramo al evaluar (no la digita el cliente)';
COMMENT ON COLUMN ms_siniestros.siniestro.requiere_revision IS 'true = el motor no resolvió el caso y queda en la cola del operador';

-- Lista del cliente (HU-160) y cola del operador (HU-26). Reemplaza el índice parcial por
-- usuario de 03_siniestro_usuario.sql por uno que además sirve el orden por fecha.
DROP INDEX IF EXISTS ms_siniestros.ix_siniestro_usuario;
CREATE INDEX ix_siniestro_usuario ON ms_siniestros.siniestro (usuario_id, creado_en DESC) WHERE usuario_id IS NOT NULL;
CREATE INDEX ix_siniestro_tipo_estado ON ms_siniestros.siniestro (tipo, estado, creado_en);

-- Parametría por ramo: reserva que se le asigna al aviso y umbral bajo el cual el pago
-- es automático. Un ramo sin fila aquí nunca se aprueba automáticamente (va a revisión).
CREATE TABLE ms_siniestros.parametro_ramo (
    ramo                    TEXT          PRIMARY KEY,
    reserva_base            NUMERIC(14,2) NOT NULL CHECK (reserva_base > 0),
    umbral_automatico       NUMERIC(14,2) NOT NULL CHECK (umbral_automatico >= 0),
    ventana_duplicado_dias  INTEGER       NOT NULL DEFAULT 30 CHECK (ventana_duplicado_dias > 0),
    actualizado_en          TIMESTAMPTZ   NOT NULL DEFAULT now()
);

INSERT INTO ms_siniestros.parametro_ramo (ramo, reserva_base, umbral_automatico) VALUES
    ('proteccion-dispositivo', 420000.00,  500000.00),
    ('vida-crediticia',        3200000.00, 500000.00),
    ('soat-motocicleta',       890000.00,  500000.00);

-- Evidencia (N6): el binario vive en S3; aquí queda la referencia ligada al usuario y al
-- siniestro. Sin columna de URL: las URLs de lectura se firman al consultar y expiran.
CREATE TABLE ms_siniestros.siniestro_adjunto (
    id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    siniestro_id     UUID          NOT NULL REFERENCES ms_siniestros.siniestro(id),
    usuario_id       UUID          NOT NULL,
    tipo             TEXT          NOT NULL,
    nombre_original  TEXT          NOT NULL,
    content_type     TEXT          NOT NULL,
    tamano_bytes     BIGINT        NOT NULL CHECK (tamano_bytes > 0),
    sha256           TEXT          NOT NULL,
    s3_bucket        TEXT          NOT NULL,
    s3_key           TEXT          NOT NULL,
    cargado_en       TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CONSTRAINT uq_siniestro_adjunto_key UNIQUE (s3_bucket, s3_key)
);

COMMENT ON COLUMN ms_siniestros.siniestro_adjunto.usuario_id IS 'ref lógica -> ms_identidad.usuario.usuario_id (quien cargó la evidencia)';

CREATE INDEX ix_siniestro_adjunto_siniestro ON ms_siniestros.siniestro_adjunto (siniestro_id);

-- Auditoría de cada decisión (HU-27, N15): quién (motor u operador), cuándo, por qué y
-- con qué reglas. Una fila por decisión; nunca se actualiza ni se borra.
CREATE TABLE ms_siniestros.siniestro_decision (
    id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    siniestro_id  UUID         NOT NULL REFERENCES ms_siniestros.siniestro(id),
    origen        TEXT         NOT NULL CHECK (origen IN ('motor', 'operador')),
    actor         TEXT         NOT NULL,
    resultado     TEXT         NOT NULL CHECK (resultado IN ('aprobado', 'rechazado', 'revision', 'enrutado')),
    motivo        TEXT,
    reglas        JSONB        NOT NULL DEFAULT '[]'::jsonb,
    decidida_en   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX ix_siniestro_decision_siniestro ON ms_siniestros.siniestro_decision (siniestro_id, decidida_en);

-- Pago del siniestro asistido (HU-29 y aprobación automática): un único desembolso por
-- siniestro; la clave de idempotencia es determinista para que un reintento devuelva el
-- mismo comprobante.
CREATE TABLE ms_siniestros.pago_siniestro (
    id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    siniestro_id        UUID          NOT NULL REFERENCES ms_siniestros.siniestro(id),
    clave_idempotencia  TEXT          NOT NULL,
    comprobante         TEXT          NOT NULL,
    monto               NUMERIC(14,2) NOT NULL CHECK (monto > 0),
    origen              TEXT          NOT NULL CHECK (origen IN ('motor', 'operador')),
    autorizado_por      TEXT          NOT NULL,
    pagado_en           TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CONSTRAINT uq_pago_siniestro_siniestro UNIQUE (siniestro_id),
    CONSTRAINT uq_pago_siniestro_clave UNIQUE (clave_idempotencia),
    CONSTRAINT uq_pago_siniestro_comprobante UNIQUE (comprobante)
);

-- Traza de cada intento de pago, incluidos los reintentos idempotentes (HU-29: "la
-- trazabilidad registra el reintento y la respuesta devuelta").
CREATE TABLE ms_siniestros.pago_siniestro_intento (
    id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    siniestro_id          UUID         NOT NULL REFERENCES ms_siniestros.siniestro(id),
    clave_idempotencia    TEXT         NOT NULL,
    resultado             TEXT         NOT NULL CHECK (resultado IN ('ejecutado', 'reintento_idempotente')),
    comprobante_devuelto  TEXT         NOT NULL,
    actor                 TEXT         NOT NULL,
    ocurrido_en           TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX ix_pago_siniestro_intento_siniestro ON ms_siniestros.pago_siniestro_intento (siniestro_id, ocurrido_en);
