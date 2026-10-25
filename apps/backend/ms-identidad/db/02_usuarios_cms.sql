\if :{?dbpass}
\else
\set dbpass 'postgres'
\endif

CREATE EXTENSION IF NOT EXISTS pgcrypto;

INSERT INTO ms_identidad.usuario (tipo_documento, numero_documento, email, password_hash, estado)
VALUES
    ('CC', '9000000001', 'asesor@solventa.co',   crypt(:'dbpass', gen_salt('bf', 12)), 'ACTIVO'),
    ('CC', '9000000002', 'operador@solventa.co', crypt(:'dbpass', gen_salt('bf', 12)), 'ACTIVO')
ON CONFLICT DO NOTHING;
