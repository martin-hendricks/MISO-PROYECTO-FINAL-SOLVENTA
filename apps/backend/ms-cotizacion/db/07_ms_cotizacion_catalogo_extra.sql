-- Seed de los otros 2 productos que el canal web ya mapea en bff-web
-- (RAMO_A_PRODUCTO en app/routers/cliente.py: "Protección de dispositivo" ->
-- proteccion-dispositivo, "Vida crediticia" -> vida-crediticia), ausentes
-- del seed original (05_ms_cotizacion_catalogo.sql solo trae SOAT). Sin este
-- seed, cotizar esos dos ramos en local responde 404 "producto_no_encontrado".

WITH dispositivo AS (
    INSERT INTO ms_cotizacion.producto (codigo, nombre, ramo, moneda)
    VALUES ('proteccion-dispositivo', 'Protección de dispositivo', 'proteccion_dispositivo', 'COP')
    RETURNING producto_id
), coberturas_dispositivo AS (
    INSERT INTO ms_cotizacion.cobertura_producto (producto_id, codigo, nombre, limite, unidad_limite, orden)
    SELECT dispositivo.producto_id, c.codigo, c.nombre, c.limite, 'MONEDA', c.orden
    FROM dispositivo, (VALUES
        ('robo',      'Robo',                        5000000, 1),
        ('dano',      'Daño accidental',             5000000, 2),
        ('reposicion', 'Reposición por equipo nuevo', 5000000, 3)
    ) AS c(codigo, nombre, limite, orden)
)
INSERT INTO ms_cotizacion.dato_riesgo_producto (producto_id, nombre, tipo, minimo, maximo, valores)
SELECT dispositivo.producto_id, d.nombre, d.tipo, d.minimo, d.maximo, d.valores
FROM dispositivo, (VALUES
    ('valorDispositivo', 'rango',   500000::NUMERIC, 10000000::NUMERIC, NULL::TEXT[]),
    ('marca',            'valores', NULL,             NULL,              ARRAY['samsung', 'apple', 'xiaomi', 'motorola'])
) AS d(nombre, tipo, minimo, maximo, valores);

WITH vida AS (
    INSERT INTO ms_cotizacion.producto (codigo, nombre, ramo, moneda)
    VALUES ('vida-crediticia', 'Vida crediticia', 'vida_crediticia', 'COP')
    RETURNING producto_id
), coberturas_vida AS (
    INSERT INTO ms_cotizacion.cobertura_producto (producto_id, codigo, nombre, limite, unidad_limite, orden)
    SELECT vida.producto_id, c.codigo, c.nombre, c.limite, 'MONEDA', c.orden
    FROM vida, (VALUES
        ('muerte',                 'Muerte por cualquier causa', 500000000, 1),
        ('incapacidad_total',      'Incapacidad total y permanente', 500000000, 2)
    ) AS c(codigo, nombre, limite, orden)
)
INSERT INTO ms_cotizacion.dato_riesgo_producto (producto_id, nombre, tipo, minimo, maximo, valores)
SELECT vida.producto_id, d.nombre, d.tipo, d.minimo, d.maximo, d.valores
FROM vida, (VALUES
    ('valorCredito', 'rango', 1000000::NUMERIC, 500000000::NUMERIC, NULL::TEXT[]),
    ('plazoMeses',   'rango', 6::NUMERIC,        360::NUMERIC,       NULL::TEXT[])
) AS d(nombre, tipo, minimo, maximo, valores);
