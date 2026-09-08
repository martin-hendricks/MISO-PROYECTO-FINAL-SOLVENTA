import orjson
from .. import db

SQL = """
SELECT
    s.numero, s.cliente_id, s.estado, s.causa,
    s.monto_estimado, s.monto_aprobado,
    s.fecha_ocurrencia, s.fecha_aviso,
    jsonb_build_object(
        'numero', p.numero,
        'producto', p.producto,
        'suma_asegurada', p.suma_asegurada
    ) AS poliza,
    COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
            'tipo', h.tipo, 'descripcion', h.descripcion,
            'actor', h.actor, 'ocurrido_en', h.ocurrido_en
        ) ORDER BY h.ocurrido_en)
        FROM siniestros_w.hito h WHERE h.siniestro_id = s.id
    ), '[]'::jsonb) AS hitos,
    COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
            'tipo', d.tipo, 'estado', d.estado, 'cargado_en', d.cargado_en
        ) ORDER BY d.cargado_en)
        FROM siniestros_w.documento d WHERE d.siniestro_id = s.id
    ), '[]'::jsonb) AS documentos,
    (
        SELECT jsonb_build_object(
            'perito', pe.perito, 'estado', pe.estado,
            'resultado', pe.resultado, 'agendado_para', pe.agendado_para
        )
        FROM siniestros_w.peritaje pe
        WHERE pe.siniestro_id = s.id
        ORDER BY pe.id DESC LIMIT 1
    ) AS peritaje
FROM siniestros_w.siniestro s
JOIN siniestros_w.poliza p ON p.id = s.poliza_id
WHERE s.id = $1
"""

async def get_estado(siniestro_id: int) -> dict | None:
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(SQL, siniestro_id)
    if row is None:
        return None
    data = dict(row)
    for k in ("poliza", "hitos", "documentos", "peritaje"):
        if isinstance(data[k], str):
            data[k] = orjson.loads(data[k])
    return data
