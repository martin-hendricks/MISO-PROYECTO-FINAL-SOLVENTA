-- Copia literal del DDL oficial: db/schema/04_ms_cotizacion.sql
-- No se edita aquí: cualquier cambio de dominio va en db/schema/04_ms_cotizacion.sql.
-- Requiere PostgreSQL 13+ (gen_random_uuid() nativo).

CREATE SCHEMA IF NOT EXISTS ms_cotizacion;

CREATE TABLE ms_cotizacion.solicitud_cotizacion (
    solicitud_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id         UUID        NOT NULL,
    socio_id           UUID        NOT NULL,
    consentimiento_id  UUID        NOT NULL,
    producto           TEXT        NOT NULL,
    canal              TEXT        NOT NULL,
    estado             TEXT        NOT NULL,
    creada_en          TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON COLUMN ms_cotizacion.solicitud_cotizacion.usuario_id IS 'ref lógica -> ms_identidad.usuario.usuario_id';
COMMENT ON COLUMN ms_cotizacion.solicitud_cotizacion.socio_id   IS 'ref lógica -> ms_socios.socio.socio_id';
COMMENT ON COLUMN ms_cotizacion.solicitud_cotizacion.consentimiento_id IS 'ref lógica -> ms_consentimiento.consentimiento_datos.consentimiento_id (ConsentimientoToken de solicitudDTO, VC-007)';

CREATE INDEX ix_solicitud_usuario ON ms_cotizacion.solicitud_cotizacion (usuario_id);
CREATE INDEX ix_solicitud_socio   ON ms_cotizacion.solicitud_cotizacion (socio_id);
CREATE INDEX ix_solicitud_consentimiento ON ms_cotizacion.solicitud_cotizacion (consentimiento_id);

CREATE TABLE ms_cotizacion.regla_rating (
    regla_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    producto  TEXT NOT NULL,
    version   TEXT NOT NULL,
    formula   TEXT NOT NULL,
    CONSTRAINT uq_regla_producto_version UNIQUE (producto, version),
    -- Destino de la FK compuesta oferta_seguro (regla_id, version_regla).
    CONSTRAINT uq_regla_id_version UNIQUE (regla_id, version)
);

CREATE TABLE ms_cotizacion.oferta_seguro (
    oferta_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    solicitud_id   UUID          NOT NULL REFERENCES ms_cotizacion.solicitud_cotizacion(solicitud_id),
    regla_id       UUID          NOT NULL,
    version_regla  TEXT          NOT NULL,
    prima          NUMERIC(14,2) NOT NULL,
    moneda         TEXT          NOT NULL,
    coberturas     TEXT          NOT NULL,
    vence_en       TIMESTAMPTZ   NOT NULL,
    -- version_regla siempre coincide con la versión de la regla aplicada.
    CONSTRAINT fk_oferta_regla FOREIGN KEY (regla_id, version_regla)
        REFERENCES ms_cotizacion.regla_rating (regla_id, version)
);

CREATE INDEX ix_oferta_solicitud ON ms_cotizacion.oferta_seguro (solicitud_id);
CREATE INDEX ix_oferta_regla     ON ms_cotizacion.oferta_seguro (regla_id);

-- Infraestructura técnica del patrón transactional outbox (no es DDL de dominio,
-- por eso no vive en db/schema/04_ms_cotizacion.sql; mismo patrón que ms-arquetipo).
CREATE TABLE ms_cotizacion.outbox_evento (
    id           UUID PRIMARY KEY,
    tipo         TEXT NOT NULL,
    agregado_id  UUID NOT NULL,
    payload      JSONB NOT NULL,
    creado_en    TIMESTAMPTZ NOT NULL DEFAULT now(),
    publicado_en TIMESTAMPTZ
);

CREATE INDEX ix_outbox_evento_pendiente
    ON ms_cotizacion.outbox_evento (creado_en) WHERE publicado_en IS NULL;
