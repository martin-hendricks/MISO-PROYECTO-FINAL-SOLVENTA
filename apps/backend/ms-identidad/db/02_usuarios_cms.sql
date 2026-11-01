INSERT INTO ms_identidad.usuario (tipo_documento, numero_documento, email, password_hash, estado)
VALUES
    ('CC', '9000000001', 'asesor@solventa.co',   '$2b$12$uutsrCk1qZ19WDcJZ1uwVO94yg0ttQlRshSgPEOPotRLN797YTfBu', 'ACTIVO'),
    ('CC', '9000000002', 'operador@solventa.co', '$2b$12$uutsrCk1qZ19WDcJZ1uwVO94yg0ttQlRshSgPEOPotRLN797YTfBu', 'ACTIVO')
ON CONFLICT DO NOTHING;
