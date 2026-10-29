-- Extensión local de ms-cotizacion (HU-163/SOLV-262): cotizaciones pendientes del asesor.
-- Aditiva y no destructiva sobre el DDL oficial (db/schema/04_ms_cotizacion.sql).
-- asesor_id: asesor que creó la cotización desde el back-office (lo deriva bff-web de la sesión).
-- cliente_ref: referencia del cliente que envió el asesor, hasta que exista ms-identidad.
-- Las filas existentes quedan en NULL y nunca se listan.
ALTER TABLE ms_cotizacion.solicitud_cotizacion
    ADD COLUMN asesor_id   UUID         NULL,
    ADD COLUMN cliente_ref VARCHAR(100) NULL;

CREATE INDEX ix_solicitud_asesor_creada
    ON ms_cotizacion.solicitud_cotizacion (asesor_id, creada_en DESC);
