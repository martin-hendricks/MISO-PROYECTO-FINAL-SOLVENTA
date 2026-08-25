# Servicios

Microservicios de la plataforma Solventa. **Vacío por ahora**: se poblará
cuando la arquitectura esté definida y los experimentos hayan arrojado
veredicto.

## Convención prevista

```
services/<nombre-del-servicio>/
├── README.md
├── Dockerfile
├── .env.example
├── pyproject.toml   (o requirements.txt)
├── app/
└── tests/
```

- Nombre en inglés, `kebab-case`, por capacidad de negocio
  (p. ej. `claims-query`, `claims-evaluation`).
- Cada servicio es desplegable de forma independiente y declara sus
  dependencias; lo compartido entre varios va a [`libs/`](../libs/).
- La composición de varios servicios para desarrollo local va a
  [`infra/`](../infra/), no dentro de un servicio.
