-- Multi ramo: descripción canónica, texto libre, sí/no y productos del canal.
ALTER TABLE ms_cotizacion.producto
    ADD COLUMN IF NOT EXISTS descripcion TEXT NOT NULL DEFAULT '';

ALTER TABLE ms_cotizacion.dato_riesgo_producto
    ADD COLUMN IF NOT EXISTS orden SMALLINT NOT NULL DEFAULT 0;

ALTER TABLE ms_cotizacion.dato_riesgo_producto DROP CONSTRAINT IF EXISTS ck_dato_riesgo_forma;
ALTER TABLE ms_cotizacion.dato_riesgo_producto DROP CONSTRAINT IF EXISTS dato_riesgo_producto_tipo_check;

ALTER TABLE ms_cotizacion.dato_riesgo_producto
    ADD CONSTRAINT dato_riesgo_producto_tipo_check CHECK (tipo IN ('rango', 'valores', 'texto', 'booleano'));

ALTER TABLE ms_cotizacion.dato_riesgo_producto
    ADD CONSTRAINT ck_dato_riesgo_forma CHECK (
        (tipo = 'rango' AND minimo IS NOT NULL AND maximo IS NOT NULL AND minimo <= maximo AND valores IS NULL)
        OR (tipo = 'valores' AND valores IS NOT NULL AND cardinality(valores) > 0 AND minimo IS NULL AND maximo IS NULL)
        OR (tipo IN ('texto', 'booleano') AND minimo IS NULL AND maximo IS NULL AND valores IS NULL)
    );

UPDATE ms_cotizacion.producto SET descripcion = 'Cubre la atención de víctimas de un accidente de tránsito en motocicleta.'
WHERE codigo = 'soat-motocicleta' AND descripcion = '';
UPDATE ms_cotizacion.producto SET descripcion = 'Cubre robo, daño accidental y reposición del equipo asegurado.'
WHERE codigo = 'proteccion-dispositivo' AND descripcion = '';
UPDATE ms_cotizacion.producto SET descripcion = 'Cubre el saldo del crédito ante muerte o incapacidad total.'
WHERE codigo = 'vida-crediticia' AND descripcion = '';

INSERT INTO ms_cotizacion.dato_riesgo_producto (producto_id, nombre, tipo, orden)
SELECT producto_id, 'modelo', 'texto', 3 FROM ms_cotizacion.producto WHERE codigo = 'proteccion-dispositivo'
AND NOT EXISTS (
    SELECT 1 FROM ms_cotizacion.dato_riesgo_producto d
    JOIN ms_cotizacion.producto p ON p.producto_id = d.producto_id
    WHERE p.codigo = 'proteccion-dispositivo' AND d.nombre = 'modelo'
);
INSERT INTO ms_cotizacion.dato_riesgo_producto (producto_id, nombre, tipo, orden)
SELECT producto_id, 'masDe12Meses', 'booleano', 4 FROM ms_cotizacion.producto WHERE codigo = 'proteccion-dispositivo'
AND NOT EXISTS (
    SELECT 1 FROM ms_cotizacion.dato_riesgo_producto d
    JOIN ms_cotizacion.producto p ON p.producto_id = d.producto_id
    WHERE p.codigo = 'proteccion-dispositivo' AND d.nombre = 'masDe12Meses'
);

INSERT INTO ms_cotizacion.producto (codigo, nombre, ramo, descripcion, moneda)
SELECT 'microseguro-de-vida', 'Microseguro de vida', 'vida',
       'Cubre a la persona asegurada según la suma y la edad declaradas.', 'COP'
WHERE NOT EXISTS (SELECT 1 FROM ms_cotizacion.producto WHERE codigo = 'microseguro-de-vida');
INSERT INTO ms_cotizacion.producto (codigo, nombre, ramo, descripcion, moneda)
SELECT 'clima-y-vuelos', 'Clima y vuelos', 'parametrico',
       'Cubre un evento climático o de vuelo cuando se supera el umbral.', 'COP'
WHERE NOT EXISTS (SELECT 1 FROM ms_cotizacion.producto WHERE codigo = 'clima-y-vuelos');
INSERT INTO ms_cotizacion.producto (codigo, nombre, ramo, descripcion, moneda)
SELECT 'vida-hipotecario', 'Vida hipotecario', 'vida_hipotecario',
       'Cubre el saldo del crédito hipotecario durante el plazo pactado.', 'COP'
WHERE NOT EXISTS (SELECT 1 FROM ms_cotizacion.producto WHERE codigo = 'vida-hipotecario');
INSERT INTO ms_cotizacion.producto (codigo, nombre, ramo, descripcion, moneda)
SELECT 'pagos', 'Pagos', 'pagos',
       'Cubre las cuotas del plan de pagos durante el plazo declarado.', 'COP'
WHERE NOT EXISTS (SELECT 1 FROM ms_cotizacion.producto WHERE codigo = 'pagos');
INSERT INTO ms_cotizacion.producto (codigo, nombre, ramo, descripcion, moneda)
SELECT 'viaje', 'Viaje', 'viaje',
       'Cubre el viaje según el destino y la duración declarados.', 'COP'
WHERE NOT EXISTS (SELECT 1 FROM ms_cotizacion.producto WHERE codigo = 'viaje');

INSERT INTO ms_cotizacion.cobertura_producto (producto_id, codigo, nombre, limite, unidad_limite, orden)
SELECT p.producto_id, c.codigo, c.nombre, c.limite, 'MONEDA', c.orden
FROM ms_cotizacion.producto p
JOIN (VALUES
    ('microseguro-de-vida', 'muerte', 'Muerte', 50000000, 1),
    ('clima-y-vuelos', 'evento', 'Evento cubierto', 2000000, 1),
    ('vida-hipotecario', 'saldo', 'Saldo del crédito', 500000000, 1),
    ('pagos', 'cuotas', 'Cuotas cubiertas', 20000000, 1),
    ('viaje', 'viaje', 'Viaje cubierto', 10000000, 1)
) AS c(producto, codigo, nombre, limite, orden) ON c.producto = p.codigo
WHERE NOT EXISTS (
    SELECT 1 FROM ms_cotizacion.cobertura_producto x
    WHERE x.producto_id = p.producto_id AND x.codigo = c.codigo
);

INSERT INTO ms_cotizacion.dato_riesgo_producto (producto_id, nombre, tipo, minimo, maximo, valores, orden)
SELECT p.producto_id, d.nombre, d.tipo, d.minimo, d.maximo, d.valores, d.orden
FROM ms_cotizacion.producto p
JOIN (VALUES
    ('microseguro-de-vida', 'sumaAsegurada', 'rango', 1000000::NUMERIC, 100000000::NUMERIC, NULL::TEXT[], 1),
    ('microseguro-de-vida', 'edad', 'rango', 18, 70, NULL, 2),
    ('clima-y-vuelos', 'evento', 'texto', NULL, NULL, NULL, 1),
    ('clima-y-vuelos', 'referencia', 'texto', NULL, NULL, NULL, 2),
    ('clima-y-vuelos', 'umbral', 'rango', 1, 1000, NULL, 3),
    ('vida-hipotecario', 'valor', 'rango', 1000000, 500000000, NULL, 1),
    ('vida-hipotecario', 'plazoMeses', 'rango', 6, 360, NULL, 2),
    ('pagos', 'cuota', 'rango', 10000, 20000000, NULL, 1),
    ('pagos', 'plazoMeses', 'rango', 1, 120, NULL, 2),
    ('viaje', 'destino', 'texto', NULL, NULL, NULL, 1),
    ('viaje', 'duracion', 'rango', 1, 365, NULL, 2)
) AS d(producto, nombre, tipo, minimo, maximo, valores, orden) ON d.producto = p.codigo
WHERE NOT EXISTS (
    SELECT 1 FROM ms_cotizacion.dato_riesgo_producto x
    WHERE x.producto_id = p.producto_id AND x.nombre = d.nombre
);

INSERT INTO ms_cotizacion.regla_rating (producto, version, formula)
SELECT producto, '0001', formula
FROM (VALUES
    ('microseguro-de-vida', '{"insumos_requeridos": ["sumaAsegurada", "edad"], "base": "45000", "gastos_fijos": "5000", "moneda": "COP"}'),
    ('clima-y-vuelos', '{"insumos_requeridos": ["umbral"], "base": "30000", "gastos_fijos": "3000", "moneda": "COP"}'),
    ('vida-hipotecario', '{"insumos_requeridos": ["valor", "plazoMeses"], "base": "180000", "gastos_fijos": "12000", "moneda": "COP"}'),
    ('pagos', '{"insumos_requeridos": ["cuota", "plazoMeses"], "base": "25000", "gastos_fijos": "2500", "moneda": "COP"}'),
    ('viaje', '{"insumos_requeridos": ["duracion"], "base": "70000", "gastos_fijos": "7000", "moneda": "COP"}')
) AS reglas(producto, formula)
WHERE NOT EXISTS (
    SELECT 1 FROM ms_cotizacion.regla_rating r
    WHERE r.producto = reglas.producto AND r.version = '0001'
);
