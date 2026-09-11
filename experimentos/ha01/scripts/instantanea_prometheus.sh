#!/usr/bin/env bash
# Instantanea consistente de toda la base de Prometheus, comprimida en
# results/prometheus/. Es el respaldo completo de las series temporales: el
# volumen de Docker no lo es, y ademas se purga a los 30 dias.
#
# Se versiona: comprimida ocupa pocos MB (4,2 MB tras el bloque 3 y el minimo
# decisivo), muy por debajo del limite de GitHub. Para restaurarla,
# descomprimirla en un directorio y arrancar un Prometheus con
# --storage.tsdb.path apuntando a el.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_comun.sh"

destino="${RAIZ}/results/prometheus"
mkdir -p "${destino}"

nombre=$(curl -sf -XPOST "http://localhost:9090/api/v1/admin/tsdb/snapshot" \
  | "${PY}" -c 'import json,sys; print(json.load(sys.stdin)["data"]["name"])') \
  || fallar "Prometheus no devolvio la instantanea (arrancado sin --web.enable-admin-api?)"

# La base vive en /prometheus/data dentro del volumen: el compose sobrescribe
# `command:` y con ello el --storage.tsdb.path de la imagen, asi que Prometheus
# usa `data/` relativo a su directorio de trabajo.
archivo="tsdb_$(date '+%Y%m%d_%H%M%S').tgz"
MSYS_NO_PATHCONV=1 docker run --rm \
  -v ha01_prom-data:/p:ro \
  -v "$(cygpath -m "${destino}"):/b" \
  alpine tar czf "/b/${archivo}" -C "/p/data/snapshots/${nombre}" .

# La instantanea ocupa espacio dentro del volumen; una vez copiada, sobra.
MSYS_NO_PATHCONV=1 docker run --rm -v ha01_prom-data:/p alpine \
  rm -rf "/p/data/snapshots/${nombre}"

echo "instantanea de Prometheus -> results/prometheus/${archivo} ($(du -h "${destino}/${archivo}" | cut -f1))"
