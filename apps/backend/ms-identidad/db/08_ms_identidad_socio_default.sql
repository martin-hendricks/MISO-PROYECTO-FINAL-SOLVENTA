INSERT INTO ms_identidad.socio (socio_id, nombre, alcances, estado)
VALUES (
    '1ebbe2fc-d8b1-4046-af76-b92bacec52ff',
    'Aliado local',
    '["catalogo:leer", "originaciones:escribir", "cotizaciones:escribir", "cotizaciones:leer"]'::jsonb,
    'activo'
)
ON CONFLICT DO NOTHING;

INSERT INTO ms_identidad.credencial_socio (credencial_id, socio_id, huella_sha256)
VALUES (
    '5b0e7c3a-2f4d-4c6e-9a81-3d7f0b2e6c14',
    '1ebbe2fc-d8b1-4046-af76-b92bacec52ff',
    '034d50a1cd9033751fc09294550c812fc0b967dce363e665f3a3ddc3f09aed63'
)
ON CONFLICT DO NOTHING;
