#!/usr/bin/env bash
# Verifica que los brazos devuelvan el mismo JSON para el mismo siniestro.
# Si difieren, parte de la latencia medida vendría del tamaño del payload
# y la comparación entre brazos quedaría invalidada.
set -euo pipefail
ID=42
for ARM in A B C; do
  READ_STRATEGY=$ARM docker compose up -d api >/dev/null
  sleep 8
  curl -s "http://localhost:8000/siniestros/${ID}/estado" | jq -S . > "/tmp/parity_${ARM}.json"
done
diff /tmp/parity_A.json /tmp/parity_B.json && diff /tmp/parity_B.json /tmp/parity_C.json \
  && echo "OK: payload idéntico entre brazos" \
  || { echo "ERROR: los brazos devuelven payloads distintos"; exit 1; }
