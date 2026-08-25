# Librerías compartidas

Código reutilizado por más de un servicio. **Vacío por ahora.**

Candidato natural a ser el primer paquete: los **contratos de eventos de
dominio** definidos en la sección 6 de la guía técnica de HA-08, que hoy
duplican productor (simulador) y consumidor (proyector).

## Regla de admisión

Algo entra aquí cuando **dos o más** servicios ya lo necesitan, no antes.
Una librería compartida prematura acopla servicios que deberían evolucionar
por separado — el mismo trade-off que el estilo de microservicios busca
evitar.

## Convención prevista

```
libs/<nombre-del-paquete>/
├── README.md
├── pyproject.toml
├── src/
└── tests/
```
