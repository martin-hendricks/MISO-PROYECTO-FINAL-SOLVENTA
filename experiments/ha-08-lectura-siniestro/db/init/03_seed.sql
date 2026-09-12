-- Pólizas
INSERT INTO siniestros_w.poliza
  (id, cliente_id, numero, producto, estado, suma_asegurada, vigencia_desde, vigencia_hasta)
SELECT g, g, 'POL-' || g,
       (ARRAY['AUTOS_TODO_RIESGO','HOGAR','VIDA','SALUD'])[1 + (g % 4)],
       'VIGENTE', 50000000 + (g % 100) * 1000000,
       DATE '2025-01-01', DATE '2026-12-31'
FROM generate_series(1, 1000000) g;

-- Siniestros
INSERT INTO siniestros_w.siniestro
  (id, poliza_id, cliente_id, numero, estado, causa, monto_estimado,
   fecha_ocurrencia, fecha_aviso, version)
SELECT g, g, g, 'SIN-2026-' || g,
       (ARRAY['RECIBIDO','EN_VALIDACION','EN_PERITAJE','EN_LIQUIDACION','APROBADO','RECHAZADO'])[1 + (g % 6)],
       (ARRAY['COLISION','HURTO','INCENDIO','DANO_AGUA'])[1 + (g % 4)],
       1000000 + (g % 500) * 10000,
       now() - (g % 365) * INTERVAL '1 day',
       now() - (g % 365) * INTERVAL '1 day' + INTERVAL '2 hours',
       1
FROM generate_series(1, 1000000) g;

-- Hitos: 5 por siniestro
INSERT INTO siniestros_w.hito (siniestro_id, tipo, descripcion, actor, ocurrido_en)
SELECT s, (ARRAY['AVISO_RECIBIDO','DOCS_SOLICITADOS','PERITO_ASIGNADO','INSPECCION','LIQUIDACION'])[h],
       'Hito automático ' || h, 'SISTEMA', now() - (h * INTERVAL '1 day')
FROM generate_series(1, 1000000) s, generate_series(1, 5) h;

-- Documentos: 3 por siniestro
INSERT INTO siniestros_w.documento (siniestro_id, tipo, estado, cargado_en)
SELECT s, (ARRAY['FOTOS','FACTURA','DENUNCIA'])[d],
       (ARRAY['PENDIENTE','APROBADO','RECHAZADO'])[1 + ((s + d) % 3)],
       now() - (d * INTERVAL '1 day')
FROM generate_series(1, 1000000) s, generate_series(1, 3) d;

-- Peritaje: 1 por siniestro
INSERT INTO siniestros_w.peritaje (siniestro_id, perito, estado, resultado, agendado_para)
SELECT s, 'P-' || (s % 500),
       (ARRAY['AGENDADO','EN_CURSO','CERRADO'])[1 + (s % 3)],
       NULL, now() + INTERVAL '1 day'
FROM generate_series(1, 1000000) s;

ANALYZE;
