-- Prestadores en los cuatro países de la app: catálogo de ciudades y país por prestador.
-- Aditivo sobre 08 e idempotente: se puede ejecutar de nuevo sin duplicar filas.

CREATE TABLE IF NOT EXISTS ms_siniestros.ciudad_prestador (
    pais    CHAR(2)       NOT NULL CHECK (pais IN ('CO', 'MX', 'CL', 'PE')),
    nombre  TEXT          NOT NULL CHECK (char_length(nombre) BETWEEN 1 AND 80),
    lat     NUMERIC(9,6)  NOT NULL CHECK (lat BETWEEN -90 AND 90),
    lng     NUMERIC(9,6)  NOT NULL CHECK (lng BETWEEN -180 AND 180),
    zoom    SMALLINT      NOT NULL CHECK (zoom BETWEEN 5 AND 18),
    orden   SMALLINT      NOT NULL CHECK (orden >= 1),
    PRIMARY KEY (pais, nombre),
    UNIQUE (pais, orden)
);

INSERT INTO ms_siniestros.ciudad_prestador (pais, orden, nombre, lat, lng, zoom) VALUES
    ('CO', 1, 'Bogotá', 4.609700, -74.081700, 12),
    ('CO', 2, 'Medellín', 6.244200, -75.581200, 13),
    ('CO', 3, 'Chía', 4.861900, -74.059700, 13),
    ('MX', 1, 'Ciudad de México', 19.432600, -99.133200, 11),
    ('MX', 2, 'Guadalajara', 20.659700, -103.349600, 13),
    ('MX', 3, 'Monterrey', 25.686600, -100.316100, 13),
    ('CL', 1, 'Santiago', -33.448900, -70.669300, 11),
    ('CL', 2, 'Valparaíso', -33.047200, -71.612700, 13),
    ('CL', 3, 'Concepción', -36.827000, -73.050300, 13),
    ('PE', 1, 'Lima', -12.046400, -77.042800, 11),
    ('PE', 2, 'Arequipa', -16.409000, -71.537500, 13),
    ('PE', 3, 'Trujillo', -8.111600, -79.028800, 13)
ON CONFLICT (pais, nombre) DO NOTHING;

-- El valor por defecto deja que 08 se vuelva a ejecutar después de este script.
ALTER TABLE ms_siniestros.prestador ADD COLUMN IF NOT EXISTS pais CHAR(2) NOT NULL DEFAULT 'CO';
ALTER TABLE ms_siniestros.prestador DROP CONSTRAINT IF EXISTS prestador_ciudad_check;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_prestador_ciudad') THEN
        ALTER TABLE ms_siniestros.prestador
            ADD CONSTRAINT fk_prestador_ciudad FOREIGN KEY (pais, ciudad)
            REFERENCES ms_siniestros.ciudad_prestador (pais, nombre);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_prestador_pais_ciudad ON ms_siniestros.prestador (pais, ciudad, estado);

INSERT INTO ms_siniestros.prestador
    (id, nombre, tipo, direccion, ciudad, pais, barrio, lat, lng, telefono, horario, estado, creado_por, actualizado_por)
VALUES
    ('PRE-CDMX-01', 'Servicio Técnico Polanco', 'servicio-tecnico', 'Av Presidente Masaryk 120', 'Ciudad de México', 'MX', 'Polanco', 19.4318, -99.1952, '55 5555 0101', 'Lun–Vie 9:00–18:00', 'activo', 'semilla', 'semilla'),
    ('PRE-CDMX-02', 'IPS Urgencias Roma Norte', 'ips-urgencias', 'Av Álvaro Obregón 85', 'Ciudad de México', 'MX', 'Roma Norte', 19.4190, -99.1615, '55 5555 0102', '24 horas', 'activo', 'semilla', 'semilla'),
    ('PRE-CDMX-03', 'IPS Exámenes Del Valle', 'ips-examenes', 'Av Insurgentes Sur 1100', 'Ciudad de México', 'MX', 'Del Valle', 19.3795, -99.1772, '55 5555 0103', 'Lun–Vie 7:00–15:00', 'activo', 'semilla', 'semilla'),
    ('PRE-CDMX-04', 'Centro de Atención Coyoacán', 'centro-atencion', 'Av Miguel Ángel de Quevedo 400', 'Ciudad de México', 'MX', 'Coyoacán', 19.3455, -99.1720, '55 5555 0104', 'Lun–Vie 9:00–17:00', 'activo', 'semilla', 'semilla'),
    ('PRE-CDMX-05', 'Punto AICM T1', 'punto-aeropuerto', 'Aeropuerto Internacional terminal 1', 'Ciudad de México', 'MX', 'Venustiano Carranza', 19.4361, -99.0719, '55 5555 0105', '24 horas', 'activo', 'semilla', 'semilla'),
    ('PRE-GDL-01', 'Servicio Técnico Providencia', 'servicio-tecnico', 'Av Pablo Neruda 2800', 'Guadalajara', 'MX', 'Providencia', 20.6935, -103.3925, '33 5555 0201', 'Lun–Vie 9:00–18:00', 'activo', 'semilla', 'semilla'),
    ('PRE-GDL-02', 'IPS Urgencias Americana', 'ips-urgencias', 'Av Chapultepec 210', 'Guadalajara', 'MX', 'Americana', 20.6712, -103.3680, '33 5555 0202', '24 horas', 'activo', 'semilla', 'semilla'),
    ('PRE-GDL-03', 'IPS Exámenes Centro Guadalajara', 'ips-examenes', 'Av Juárez 450', 'Guadalajara', 'MX', 'Centro', 20.6748, -103.3530, '33 5555 0203', 'Lun–Vie 7:00–15:00', 'activo', 'semilla', 'semilla'),
    ('PRE-GDL-04', 'Centro de Atención Chapalita', 'centro-atencion', 'Av Guadalupe 1200', 'Guadalajara', 'MX', 'Chapalita', 20.6650, -103.4020, '33 5555 0204', 'Lun–Vie 9:00–17:00', 'activo', 'semilla', 'semilla'),
    ('PRE-MTY-01', 'Servicio Técnico San Jerónimo', 'servicio-tecnico', 'Av San Jerónimo 900', 'Monterrey', 'MX', 'San Jerónimo', 25.6765, -100.3645, '81 5555 0301', 'Lun–Vie 9:00–18:00', 'activo', 'semilla', 'semilla'),
    ('PRE-MTY-02', 'IPS Urgencias Obispado', 'ips-urgencias', 'Av Hidalgo 2400', 'Monterrey', 'MX', 'Obispado', 25.6752, -100.3398, '81 5555 0302', '24 horas', 'activo', 'semilla', 'semilla'),
    ('PRE-MTY-03', 'IPS Exámenes Centro Monterrey', 'ips-examenes', 'Av Constitución 300', 'Monterrey', 'MX', 'Centro', 25.6698, -100.3095, '81 5555 0303', 'Lun–Vie 7:00–15:00', 'activo', 'semilla', 'semilla'),
    ('PRE-MTY-04', 'Centro de Atención Contry', 'centro-atencion', 'Av Revolución 3800', 'Monterrey', 'MX', 'Contry', 25.6310, -100.2810, '81 5555 0304', 'Lun–Vie 9:00–17:00', 'activo', 'semilla', 'semilla'),
    ('PRE-SCL-01', 'Servicio Técnico Providencia', 'servicio-tecnico', 'Av Providencia 1650', 'Santiago', 'CL', 'Providencia', -33.4310, -70.6105, '+56 2 5555 0101', 'Lun–Vie 9:00–18:00', 'activo', 'semilla', 'semilla'),
    ('PRE-SCL-02', 'IPS Urgencias Las Condes', 'ips-urgencias', 'Av Apoquindo 4500', 'Santiago', 'CL', 'Las Condes', -33.4152, -70.5835, '+56 2 5555 0102', '24 horas', 'activo', 'semilla', 'semilla'),
    ('PRE-SCL-03', 'IPS Exámenes Ñuñoa', 'ips-examenes', 'Av Irarrázaval 3200', 'Santiago', 'CL', 'Ñuñoa', -33.4565, -70.5975, '+56 2 5555 0103', 'Lun–Vie 7:30–15:30', 'activo', 'semilla', 'semilla'),
    ('PRE-SCL-04', 'Centro de Atención Santiago Centro', 'centro-atencion', 'Paseo Ahumada 250', 'Santiago', 'CL', 'Santiago Centro', -33.4405, -70.6505, '+56 2 5555 0104', 'Lun–Vie 9:00–17:00', 'activo', 'semilla', 'semilla'),
    ('PRE-SCL-05', 'Punto Arturo Merino Benítez', 'punto-aeropuerto', 'Aeropuerto Arturo Merino Benítez terminal 2', 'Santiago', 'CL', 'Pudahuel', -33.3930, -70.7858, '+56 2 5555 0105', '24 horas', 'activo', 'semilla', 'semilla'),
    ('PRE-VAP-01', 'Servicio Técnico Plan de Valparaíso', 'servicio-tecnico', 'Av Pedro Montt 1800', 'Valparaíso', 'CL', 'Plan', -33.0462, -71.6195, '+56 32 555 0201', 'Lun–Vie 9:00–18:00', 'activo', 'semilla', 'semilla'),
    ('PRE-VAP-02', 'IPS Urgencias Playa Ancha', 'ips-urgencias', 'Av Playa Ancha 400', 'Valparaíso', 'CL', 'Playa Ancha', -33.0300, -71.6385, '+56 32 555 0202', '24 horas', 'activo', 'semilla', 'semilla'),
    ('PRE-VAP-03', 'IPS Exámenes Cerro Alegre', 'ips-examenes', 'Calle Templeman 150', 'Valparaíso', 'CL', 'Cerro Alegre', -33.0430, -71.6270, '+56 32 555 0203', 'Lun–Vie 7:30–15:30', 'activo', 'semilla', 'semilla'),
    ('PRE-VAP-04', 'Centro de Atención Barón', 'centro-atencion', 'Av Argentina 50', 'Valparaíso', 'CL', 'Barón', -33.0405, -71.6010, '+56 32 555 0204', 'Lun–Vie 9:00–17:00', 'activo', 'semilla', 'semilla'),
    ('PRE-CCP-01', 'Servicio Técnico Concepción Centro', 'servicio-tecnico', 'Calle Barros Arana 800', 'Concepción', 'CL', 'Centro', -36.8275, -73.0505, '+56 41 555 0301', 'Lun–Vie 9:00–18:00', 'activo', 'semilla', 'semilla'),
    ('PRE-CCP-02', 'IPS Urgencias Pedro de Valdivia', 'ips-urgencias', 'Av Pedro de Valdivia 1200', 'Concepción', 'CL', 'Pedro de Valdivia', -36.8450, -73.0630, '+56 41 555 0302', '24 horas', 'activo', 'semilla', 'semilla'),
    ('PRE-CCP-03', 'IPS Exámenes Barrio Universitario', 'ips-examenes', 'Av Chacabuco 1500', 'Concepción', 'CL', 'Barrio Universitario', -36.8292, -73.0365, '+56 41 555 0303', 'Lun–Vie 7:30–15:30', 'activo', 'semilla', 'semilla'),
    ('PRE-CCP-04', 'Centro de Atención Lorenzo Arenas', 'centro-atencion', 'Av Los Carrera 300', 'Concepción', 'CL', 'Lorenzo Arenas', -36.8055, -73.0550, '+56 41 555 0304', 'Lun–Vie 9:00–17:00', 'activo', 'semilla', 'semilla'),
    ('PRE-LIM-01', 'Servicio Técnico Miraflores', 'servicio-tecnico', 'Av Larco 700', 'Lima', 'PE', 'Miraflores', -12.1215, -77.0300, '01 555 0101', 'Lun–Vie 9:00–18:00', 'activo', 'semilla', 'semilla'),
    ('PRE-LIM-02', 'IPS Urgencias San Isidro', 'ips-urgencias', 'Av Javier Prado Oeste 1200', 'Lima', 'PE', 'San Isidro', -12.0972, -77.0365, '01 555 0102', '24 horas', 'activo', 'semilla', 'semilla'),
    ('PRE-LIM-03', 'IPS Exámenes Surco', 'ips-examenes', 'Av Primavera 900', 'Lima', 'PE', 'Santiago de Surco', -12.1395, -76.9955, '01 555 0103', 'Lun–Vie 7:00–15:00', 'activo', 'semilla', 'semilla'),
    ('PRE-LIM-04', 'Centro de Atención Cercado', 'centro-atencion', 'Jr de la Unión 500', 'Lima', 'PE', 'Cercado de Lima', -12.0465, -77.0305, '01 555 0104', 'Lun–Vie 9:00–17:00', 'activo', 'semilla', 'semilla'),
    ('PRE-LIM-05', 'Punto Jorge Chávez', 'punto-aeropuerto', 'Aeropuerto Jorge Chávez sala nacional', 'Lima', 'PE', 'Callao', -12.0219, -77.1143, '01 555 0105', '24 horas', 'activo', 'semilla', 'semilla'),
    ('PRE-AQP-01', 'Servicio Técnico Cercado Arequipa', 'servicio-tecnico', 'Calle Mercaderes 200', 'Arequipa', 'PE', 'Cercado', -16.3992, -71.5365, '054 555 0201', 'Lun–Vie 9:00–18:00', 'activo', 'semilla', 'semilla'),
    ('PRE-AQP-02', 'IPS Urgencias Yanahuara', 'ips-urgencias', 'Av Ejército 300', 'Arequipa', 'PE', 'Yanahuara', -16.3885, -71.5455, '054 555 0202', '24 horas', 'activo', 'semilla', 'semilla'),
    ('PRE-AQP-03', 'IPS Exámenes Cayma', 'ips-examenes', 'Av Cayma 500', 'Arequipa', 'PE', 'Cayma', -16.3705, -71.5450, '054 555 0203', 'Lun–Vie 7:00–15:00', 'activo', 'semilla', 'semilla'),
    ('PRE-AQP-04', 'Centro de Atención Cerro Colorado', 'centro-atencion', 'Av Aviación 600', 'Arequipa', 'PE', 'Cerro Colorado', -16.3725, -71.5655, '054 555 0204', 'Lun–Vie 9:00–17:00', 'activo', 'semilla', 'semilla'),
    ('PRE-TRU-01', 'Servicio Técnico Centro Trujillo', 'servicio-tecnico', 'Jr Pizarro 400', 'Trujillo', 'PE', 'Centro', -8.1118, -79.0285, '044 555 0301', 'Lun–Vie 9:00–18:00', 'activo', 'semilla', 'semilla'),
    ('PRE-TRU-02', 'IPS Urgencias California', 'ips-urgencias', 'Av Larco 1100', 'Trujillo', 'PE', 'California', -8.1005, -79.0405, '044 555 0302', '24 horas', 'activo', 'semilla', 'semilla'),
    ('PRE-TRU-03', 'IPS Exámenes Primavera', 'ips-examenes', 'Av América Norte 800', 'Trujillo', 'PE', 'Primavera', -8.1052, -79.0175, '044 555 0303', 'Lun–Vie 7:00–15:00', 'activo', 'semilla', 'semilla'),
    ('PRE-TRU-04', 'Centro de Atención El Golf', 'centro-atencion', 'Av Juan Pablo II 1500', 'Trujillo', 'PE', 'El Golf', -8.1340, -79.0400, '044 555 0304', 'Lun–Vie 9:00–17:00', 'activo', 'semilla', 'semilla')
ON CONFLICT (id) DO NOTHING;

INSERT INTO ms_siniestros.prestador_ramo (prestador_id, ramo) VALUES
    ('PRE-CDMX-01', 'proteccion-dispositivo'),
    ('PRE-CDMX-02', 'viaje'),
    ('PRE-CDMX-03', 'microseguro-de-vida'),
    ('PRE-CDMX-03', 'vida-crediticia'),
    ('PRE-CDMX-03', 'vida-hipotecario'),
    ('PRE-CDMX-04', 'pagos'),
    ('PRE-CDMX-05', 'clima-y-vuelos'),
    ('PRE-GDL-01', 'proteccion-dispositivo'),
    ('PRE-GDL-02', 'viaje'),
    ('PRE-GDL-03', 'microseguro-de-vida'),
    ('PRE-GDL-03', 'vida-crediticia'),
    ('PRE-GDL-03', 'vida-hipotecario'),
    ('PRE-GDL-04', 'pagos'),
    ('PRE-MTY-01', 'proteccion-dispositivo'),
    ('PRE-MTY-02', 'viaje'),
    ('PRE-MTY-03', 'microseguro-de-vida'),
    ('PRE-MTY-03', 'vida-crediticia'),
    ('PRE-MTY-03', 'vida-hipotecario'),
    ('PRE-MTY-04', 'pagos'),
    ('PRE-SCL-01', 'proteccion-dispositivo'),
    ('PRE-SCL-02', 'viaje'),
    ('PRE-SCL-03', 'microseguro-de-vida'),
    ('PRE-SCL-03', 'vida-crediticia'),
    ('PRE-SCL-03', 'vida-hipotecario'),
    ('PRE-SCL-04', 'pagos'),
    ('PRE-SCL-05', 'clima-y-vuelos'),
    ('PRE-VAP-01', 'proteccion-dispositivo'),
    ('PRE-VAP-02', 'viaje'),
    ('PRE-VAP-03', 'microseguro-de-vida'),
    ('PRE-VAP-03', 'vida-crediticia'),
    ('PRE-VAP-03', 'vida-hipotecario'),
    ('PRE-VAP-04', 'pagos'),
    ('PRE-CCP-01', 'proteccion-dispositivo'),
    ('PRE-CCP-02', 'viaje'),
    ('PRE-CCP-03', 'microseguro-de-vida'),
    ('PRE-CCP-03', 'vida-crediticia'),
    ('PRE-CCP-03', 'vida-hipotecario'),
    ('PRE-CCP-04', 'pagos'),
    ('PRE-LIM-01', 'proteccion-dispositivo'),
    ('PRE-LIM-02', 'viaje'),
    ('PRE-LIM-03', 'microseguro-de-vida'),
    ('PRE-LIM-03', 'vida-crediticia'),
    ('PRE-LIM-03', 'vida-hipotecario'),
    ('PRE-LIM-04', 'pagos'),
    ('PRE-LIM-05', 'clima-y-vuelos'),
    ('PRE-AQP-01', 'proteccion-dispositivo'),
    ('PRE-AQP-02', 'viaje'),
    ('PRE-AQP-03', 'microseguro-de-vida'),
    ('PRE-AQP-03', 'vida-crediticia'),
    ('PRE-AQP-03', 'vida-hipotecario'),
    ('PRE-AQP-04', 'pagos'),
    ('PRE-TRU-01', 'proteccion-dispositivo'),
    ('PRE-TRU-02', 'viaje'),
    ('PRE-TRU-03', 'microseguro-de-vida'),
    ('PRE-TRU-03', 'vida-crediticia'),
    ('PRE-TRU-03', 'vida-hipotecario'),
    ('PRE-TRU-04', 'pagos')
ON CONFLICT (prestador_id, ramo) DO NOTHING;
