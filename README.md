# MISO — Proyecto final — Solventa

Monorepo del proyecto final de la Maestría en Ingeniería de Software
(**MISW4501 — Arquitectura de Software**), caso de estudio **Solventa**,
plataforma insurtech.

El repositorio aloja hoy los **experimentos de arquitectura** y, a medida que
la arquitectura se defina, los **servicios** que la implementan, conviviendo
bajo las mismas convenciones.

## Estructura

| Carpeta | Contenido |
|---|---|
| [`docs/`](docs/) | Documentación de arquitectura: vistas, ADRs y diseños de experimento. |
| [`experiments/`](experiments/) | Experimentos de arquitectura, uno por carpeta y autocontenidos. |
| [`services/`](services/) | Microservicios de Solventa. Vacío hasta que se defina la arquitectura. |
| [`libs/`](libs/) | Código compartido entre servicios: contratos de eventos, utilidades. |
| [`infra/`](infra/) | Infraestructura transversal: compose/k8s, observabilidad compartida. |

## Estado actual

| Trabajo | Ubicación | Estado |
|---|---|---|
| **HA-08** — Modelo de lectura de baja latencia (CQRS + caché) | [`experiments/ha-08-cqrs-read-model/`](experiments/ha-08-cqrs-read-model/) | 🚧 Estructura creada, implementación pendiente |

Diseño y guía técnica de HA-08: [`docs/experiments/ha-08/`](docs/experiments/ha-08/).

## Convenciones

- **Nombres de carpeta:** inglés, `kebab-case`. Los documentos y el contenido
  siguen en español.
- **Autocontención:** cada experimento y cada servicio trae su propio
  `docker-compose.yml`, `Dockerfile` y `.env.example`, y se ejecuta con **su
  carpeta como directorio de trabajo**. No hay un compose único en la raíz.
- **Configuración:** solo se versiona `.env.example`; el `.env` real está
  ignorado.
- **Fin de línea:** `.gitattributes` fuerza LF en scripts, código y SQL. Es
  obligatorio en Windows — un CRLF rompe los `.sh` dentro de los contenedores.
- **Ramas:** `feature/<tema>` desde `main`.

## Primeros pasos

```bash
git clone <url> && cd MISO-PROYECTO-FINAL-SOLVENTA
cd experiments/ha-08-cqrs-read-model
cp .env.example .env
docker compose up -d
```

> **Nota para Windows.** Los scripts son `.sh` y requieren **Git Bash**. Si el
> clon vive dentro de OneDrive, evitar bind mounts de datos dentro del repo:
> la sincronización degrada las mediciones de latencia.

## Equipo

| Integrante | Rol en HA-08 |
|---|---|
| Alex Mauricio Rodriguez Sanchez | API de Consulta de Siniestros |
| Martin Ricardo Romero Ortiz | Entorno de ejecución y observabilidad |
| Pedro Camilo Rojas Puertas | Proyector y simulador |
| Juan Camilo Acevedo Ospina | Diseño, dataset, carga y análisis |
