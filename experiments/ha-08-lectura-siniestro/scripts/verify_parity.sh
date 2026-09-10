#!/usr/bin/env bash
# Verifica que los brazos devuelvan el mismo JSON para el mismo siniestro.
# Si difieren, parte de la latencia medida vendría del tamaño del payload
# y la comparación entre brazos quedaría invalidada.
#
# IMPORTANTE: este script recrea el contenedor "api" con A, B y C en un
# bucle, y lo deja arrancado con el ÚLTIMO brazo del bucle (C). Por eso debe
# ejecutarse UNA SOLA VEZ antes de toda la serie de corridas (no dentro de
# run_experiment.sh ni de run_experiment_alta_carga.sh), y run_experiment.sh
# vuelve a levantar la API con el brazo correcto en su propio paso 2 después
# de esto. Un fallo detectado en la evaluación de la ejecución del
# 2026-09-10 (ver EVALUACION_EJECUCION_HA-08.md) fue precisamente invocar
# este script DENTRO de cada corrida, después de levantar el brazo correcto:
# la API quedaba en C justo antes de que k6 midiera, así que las 12 corridas
# formales terminaron midiendo todas el brazo C. La aserción sobre /health
# en run_experiment.sh (paso 3) existe para que ese error no pueda repetirse
# en silencio.
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
