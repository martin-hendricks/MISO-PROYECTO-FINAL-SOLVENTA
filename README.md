# MISO-PROYECTO-FINAL-SOLVENTA

Proyecto final de la maestría en ingeniería de software, caso Solventa: aseguradora digital insurtech. Documentación completa (enunciado, backlog, decisiones de arquitectura, estrategia de pruebas) en la [wiki](https://github.com/juancamiloacevedo/MISO-PROYECTO-FINAL-SOLVENTA/wiki) del repositorio.

## Estructura

Monorepo con un folder por aplicación/componente desplegable:

```
apps/
├── web/            # Cliente web — AngularJS/TypeScript
├── mobile/         # Cliente móvil — Android Kotlin/Jetpack Compose
└── backend/        # Núcleo de dominio — Python, un folder por microservicio
    ├── ms-cotizacion/
    ├── ms-suscripcion/
    ├── ms-polizas/
    ├── ms-siniestros/
    ├── ms-parametrico/
    ├── ms-perfilamiento/
    ├── ms-consentimiento/
    ├── ms-identidad/
    ├── ms-pagos/
    ├── bff-web/
    ├── bff-movil/
    └── api-socios/

experiments/
└── ha-08-lectura-siniestro/   # Experimento de arquitectura HA-08 (CQRS, EC-LAT-11)

infra/
└── terraform/      # IaC de la infraestructura AWS (ambiente mínimo + ambiente de experimentos)

docs/                # Artefactos técnicos versionados junto al código
```

Cada app/microservicio es independiente en build y despliegue; no comparten build tool entre Python, Angular y Kotlin.
