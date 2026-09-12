#!/usr/bin/env bash
# Repite la iteración de alta carga (150/300/600 req/s) para los 3 brazos
# con el script ya corregido (aserción de /health + captura de cache_*.txt).
# La ejecución anterior (2026-09-09) quedó invalidada por el mismo defecto
# que las 12 corridas del protocolo formal — ver INFORME.md §0.
set -euo pipefail

for ARM in A B C; do
  echo ""
  echo "================================================================"
  echo "  [Alta carga] Corrida alta_carga_v2, brazo ${ARM}  ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
  echo "================================================================"
  ./scripts/run_experiment_alta_carga.sh "${ARM}" alta_carga_v2
done

echo ""
echo "==> Serie de alta carga (3 corridas) finalizada sin errores."
