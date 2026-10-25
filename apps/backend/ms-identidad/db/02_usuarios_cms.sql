-- Usuarios del CMS (asesor y operador). Se aplica en local (initdb.d) y en
-- despliegue (run-migrations.sh, una sola vez vía schema_migrations).
--
-- La contraseña no está en el repo: es la contraseña de la base que trae el
-- secreto database_url, que run-migrations.sh pasa como variable dbpass.
-- Sin esa variable (initdb.d de docker-compose) se usa la del compose.
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
