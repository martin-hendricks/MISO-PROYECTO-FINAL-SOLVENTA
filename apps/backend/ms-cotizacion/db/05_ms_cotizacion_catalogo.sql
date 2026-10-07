-- Extensión local de ms-cotizacion sobre el DDL oficial (db/schema/04_ms_cotizacion.sql).
-- No modifica el archivo oficial: lo complementa de forma aditiva y no destructiva.
-- Catálogo mínimo de productos (HU-1/SOLV-94): un ramo con coberturas fijas, sus límites,
-- su moneda y el rango válido de cada dato del riesgo. Es de solo lectura en ejecución:
-- el servicio lo carga al arrancar y ningún canal da de alta ni edita productos.
-- Agregar un ramo es insertar filas aquí, no cambiar código (EC-MOD-01).

CREATE TABLE ms_cotizacion.producto (
    producto_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Mismo valor que solicitud_cotizacion.producto y regla_rating.producto.
    codigo       TEXT NOT NULL,
    nombre       TEXT NOT NULL,
    ramo         TEXT NOT NULL,
    moneda       TEXT NOT NULL CHECK (moneda ~ '^[A-Z]{3}$'),
    CONSTRAINT uq_producto_codigo UNIQUE (codigo)
);

CREATE TABLE ms_cotizacion.cobertura_producto (
    cobertura_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id   UUID          NOT NULL REFERENCES ms_cotizacion.producto(producto_id),
    codigo        TEXT          NOT NULL,
    nombre        TEXT          NOT NULL,
    limite        NUMERIC(14,2) NOT NULL CHECK (limite > 0),
    -- SMLDV: salarios mínimos legales diarios vigentes (así fija la norma los topes del SOAT).
    -- MONEDA: el límite está expresado en la moneda del producto.
    unidad_limite TEXT          NOT NULL CHECK (unidad_limite IN ('SMLDV', 'MONEDA')),
    orden         SMALLINT      NOT NULL,
    CONSTRAINT uq_cobertura_producto_codigo UNIQUE (producto_id, codigo)
);

CREATE TABLE ms_cotizacion.dato_riesgo_producto (
    dato_riesgo_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    producto_id    UUID          NOT NULL REFERENCES ms_cotizacion.producto(producto_id),
    nombre         TEXT          NOT NULL,
    tipo           TEXT          NOT NULL CHECK (tipo IN ('rango', 'valores')),
    minimo         NUMERIC(14,2),
    maximo         NUMERIC(14,2),
    valores        TEXT[],
    CONSTRAINT uq_dato_riesgo_producto_nombre UNIQUE (producto_id, nombre),
    CONSTRAINT ck_dato_riesgo_forma CHECK (
        (tipo = 'rango' AND minimo IS NOT NULL AND maximo IS NOT NULL AND minimo <= maximo AND valores IS NULL)
        OR (tipo = 'valores' AND valores IS NOT NULL AND cardinality(valores) > 0 AND minimo IS NULL AND maximo IS NULL)
    )
);

CREATE INDEX ix_cobertura_producto ON ms_cotizacion.cobertura_producto (producto_id);
CREATE INDEX ix_dato_riesgo_producto ON ms_cotizacion.dato_riesgo_producto (producto_id);

-- Semilla: SOAT motocicleta. Topes de cobertura en SMLDV según el Decreto 056 de 2015.
WITH soat AS (
    INSERT INTO ms_cotizacion.producto (codigo, nombre, ramo, moneda)
    VALUES ('soat-motocicleta', 'SOAT motocicleta', 'soat', 'COP')
    RETURNING producto_id
), coberturas AS (
    INSERT INTO ms_cotizacion.cobertura_producto (producto_id, codigo, nombre, limite, unidad_limite, orden)
    SELECT soat.producto_id, c.codigo, c.nombre, c.limite, 'SMLDV', c.orden
    FROM soat, (VALUES
        ('gastos_medicos',         'Gastos médicos, quirúrgicos, farmacéuticos y hospitalarios', 800, 1),
        ('incapacidad_permanente', 'Incapacidad permanente',                                     180, 2),
        ('muerte',                 'Muerte y gastos funerarios',                                 750, 3),
        ('gastos_transporte',      'Gastos de transporte y movilización de víctimas',             10, 4)
    ) AS c(codigo, nombre, limite, orden)
)
INSERT INTO ms_cotizacion.dato_riesgo_producto (producto_id, nombre, tipo, minimo, maximo, valores)
SELECT soat.producto_id, d.nombre, d.tipo, d.minimo, d.maximo, d.valores
FROM soat, (VALUES
    ('cilindraje_cc',      'rango',   50::NUMERIC,   1800::NUMERIC, NULL::TEXT[]),
    ('modelo_anio',        'rango',   2000,          2026,          NULL),
    ('ciudad_circulacion', 'valores', NULL,          NULL,          ARRAY['bogota', 'medellin', 'cali', 'barranquilla', 'bucaramanga'])
) AS d(nombre, tipo, minimo, maximo, valores);
