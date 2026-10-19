-- Extensión local de ms-cotizacion sobre el DDL oficial (db/schema/04_ms_cotizacion.sql).
-- No modifica el archivo oficial: lo complementa de forma aditiva y no destructiva.
-- prima_neta/gastos_expedicion: desglose que HU-6/SOLV-99 exige devolver al canal.
-- El DDL oficial solo tiene `prima` (total).
ALTER TABLE ms_cotizacion.oferta_seguro
    ADD COLUMN prima_neta        NUMERIC(14,2) NOT NULL DEFAULT 0,
    ADD COLUMN gastos_expedicion NUMERIC(14,2) NOT NULL DEFAULT 0;

-- Regla de rating de ejemplo para SOAT motocicleta, usada por pruebas de integración
-- y por desarrollo local. formula es TEXT con JSON serializado (campo oficial, libre).
INSERT INTO ms_cotizacion.regla_rating (producto, version, formula) VALUES (
    'soat-motocicleta',
    '0001',
    '{"insumos_requeridos": ["cilindraje_cc"], "base": "120000", "gastos_fijos": "8500", "moneda": "COP"}'
);
