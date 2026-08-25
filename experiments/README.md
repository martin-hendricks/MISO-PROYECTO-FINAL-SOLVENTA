# Experimentos de arquitectura

Cada experimento valida una hipótesis de diseño asociada a una historia de
arquitectura y a un ASR. Un experimento por carpeta, **autocontenido**: su
propio `docker-compose.yml`, sus `Dockerfile`, su `.env.example` y sus
scripts.

| Experimento | Historia | ASR | Hipótesis | Estado |
|---|---|---|---|---|
| [`ha-08-cqrs-read-model/`](ha-08-cqrs-read-model/) | HA-08 | EC-LAT-11 — Latencia (A,A) | HD-08 | 🚧 Estructura creada |

## Cómo agregar uno nuevo

1. Crear `experiments/<ha-NN>-<descripcion-corta-en-kebab-case>/`.
2. Escribir el diseño y la guía técnica en `docs/experiments/<ha-NN>/`.
3. Partir de la estructura de HA-08: `api/`, `db/init/`, `load/`,
   `observability/`, `scripts/`, `results/raw/`.
4. Versionar `.env.example`, nunca `.env`. Mantener `results/raw/` ignorado.
5. Registrarlo en la tabla de arriba y en el README de la raíz.

## Reglas de ejecución

- Los comandos se ejecutan con la **carpeta del experimento** como directorio
  de trabajo: todas las rutas de las guías son relativas a ella.
- Los experimentos no comparten puertos ni volúmenes: **no ejecutar dos a la
  vez**, y menos aún al medir latencia.
- Los volúmenes de datos son *named volumes* de Docker, nunca bind mounts
  dentro del repositorio.
