-- Precarga la proyección de lectura ejecutando la misma consulta del brazo A
-- para todos los siniestros. Los brazos B y C parten de un estado completo
-- y no miden fallos masivos que no ocurrirían en producción.

INSERT INTO siniestros_r.siniestro_estado
    (siniestro_id, cliente_id, version, ocurrido_en, proyectado_en, payload)
SELECT
    s.id,
    s.cliente_id,
    s.version,
    s.actualizado_en,
    now(),
    jsonb_build_object(
        'numero', s.numero,
        'cliente_id', s.cliente_id,
        'estado', s.estado,
        'causa', s.causa,
        'monto_estimado', s.monto_estimado,
        'monto_aprobado', s.monto_aprobado,
        'fecha_ocurrencia', s.fecha_ocurrencia,
        'fecha_aviso', s.fecha_aviso,
        'poliza', jsonb_build_object(
            'numero', p.numero,
            'producto', p.producto,
            'suma_asegurada', p.suma_asegurada
        ),
        'hitos', COALESCE((
            SELECT jsonb_agg(jsonb_build_object(
                'tipo', h.tipo, 'descripcion', h.descripcion,
                'actor', h.actor, 'ocurrido_en', h.ocurrido_en
            ) ORDER BY h.ocurrido_en)
            FROM siniestros_w.hito h WHERE h.siniestro_id = s.id
        ), '[]'::jsonb),
        'documentos', COALESCE((
            SELECT jsonb_agg(jsonb_build_object(
                'tipo', d.tipo, 'estado', d.estado, 'cargado_en', d.cargado_en
            ) ORDER BY d.cargado_en)
            FROM siniestros_w.documento d WHERE d.siniestro_id = s.id
        ), '[]'::jsonb),
        'peritaje', (
            SELECT jsonb_build_object(
                'perito', pe.perito, 'estado', pe.estado,
                'resultado', pe.resultado, 'agendado_para', pe.agendado_para
            )
            FROM siniestros_w.peritaje pe
            WHERE pe.siniestro_id = s.id
            ORDER BY pe.id DESC LIMIT 1
        )
    )
FROM siniestros_w.siniestro s
JOIN siniestros_w.poliza p ON p.id = s.poliza_id
ON CONFLICT (siniestro_id) DO NOTHING;

ANALYZE siniestros_r.siniestro_estado;
