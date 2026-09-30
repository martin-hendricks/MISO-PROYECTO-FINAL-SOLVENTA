-- Solventa — Modelo de datos (VC-004, wiki §1.1.4.1)
-- Un schema PostgreSQL por microservicio/almacén propio.
-- Las referencias marcadas "(ref)" en el modelo cruzan límites de servicio y se
-- implementan como FK lógicas: columna UUID + índice + COMMENT, sin constraint.
-- Requiere PostgreSQL 13+ (gen_random_uuid() nativo).

CREATE SCHEMA IF NOT EXISTS ms_identidad;
CREATE SCHEMA IF NOT EXISTS ms_consentimiento;
CREATE SCHEMA IF NOT EXISTS ms_socios;
CREATE SCHEMA IF NOT EXISTS ms_cotizacion;
CREATE SCHEMA IF NOT EXISTS ms_perfilamiento;
CREATE SCHEMA IF NOT EXISTS ms_suscripcion;
CREATE SCHEMA IF NOT EXISTS ms_polizas;
CREATE SCHEMA IF NOT EXISTS ms_siniestros;
CREATE SCHEMA IF NOT EXISTS ms_pagos;
CREATE SCHEMA IF NOT EXISTS ms_parametrico;
CREATE SCHEMA IF NOT EXISTS analitica;
CREATE SCHEMA IF NOT EXISTS notificaciones;
