-- Reglas de rating para los productos agregados en
-- 07_ms_cotizacion_catalogo_extra.sql -- sin esto, cotizar esos ramos falla
-- con "regla_rating_no_configurada" (ver app/domain/rating.py: calcular_prima
-- exige una ReglaRating por producto antes de poder calcular la prima).
INSERT INTO ms_cotizacion.regla_rating (producto, version, formula) VALUES (
    'proteccion-dispositivo',
    '0001',
    '{"insumos_requeridos": ["valorDispositivo"], "base": "89000", "gastos_fijos": "9000", "moneda": "COP"}'
);

INSERT INTO ms_cotizacion.regla_rating (producto, version, formula) VALUES (
    'vida-crediticia',
    '0001',
    '{"insumos_requeridos": ["valorCredito", "plazoMeses"], "base": "150000", "gastos_fijos": "12000", "moneda": "COP"}'
);
