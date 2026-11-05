ALTER TABLE ms_identidad.usuario
    ADD COLUMN IF NOT EXISTS rol TEXT NOT NULL DEFAULT 'cliente';

ALTER TABLE ms_identidad.usuario DROP CONSTRAINT IF EXISTS ck_usuario_rol;
ALTER TABLE ms_identidad.usuario
    ADD CONSTRAINT ck_usuario_rol CHECK (rol IN ('cliente', 'asesor', 'operador'));

UPDATE ms_identidad.usuario
SET rol = 'operador'
WHERE lower(email) LIKE 'operador%' AND rol = 'cliente';

UPDATE ms_identidad.usuario
SET rol = 'asesor'
WHERE rol = 'cliente'
  AND (lower(email) LIKE '%@solventa.co' OR lower(email) LIKE '%@solventa.com');
