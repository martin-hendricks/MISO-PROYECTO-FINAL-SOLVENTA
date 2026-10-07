#!/usr/bin/env bash
set -euo pipefail

uso() {
  echo "Uso: $0 <ms|bff> <nombre>   (ej: $0 ms ms-cotizacion | $0 bff bff-web)" >&2
  exit 2
}

[[ $# -eq 2 ]] || uso
tipo="$1"
nombre="$2"

[[ "$tipo" == "ms" || "$tipo" == "bff" ]] || uso
prefijos="$tipo"
[[ "$tipo" == "bff" ]] && prefijos="bff|api"
if [[ ! "$nombre" =~ ^(${prefijos})-[a-z][a-z0-9]*(-[a-z0-9]+)*$ ]]; then
  echo "Nombre inválido: '$nombre' debe empezar por '${prefijos//|/- o }-' y usar minúsculas, números y guiones." >&2
  exit 2
fi
if [[ "$nombre" == "${tipo}-arquetipo" ]]; then
  echo "'$nombre' es el arquetipo mismo." >&2
  exit 2
fi

backend="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
origen="$backend/${tipo}-arquetipo"
destino="$backend/$nombre"
arquetipo="${tipo}-arquetipo"
arquetipo_snake="${tipo}_arquetipo"
nombre_snake="${nombre//-/_}"
marcador="<!-- desarrollo -->"

[[ -d "$origen" ]] || { echo "No existe el arquetipo $origen" >&2; exit 1; }

readme_previo=""
if [[ -d "$destino" ]]; then
  otros="$(ls -A "$destino" | grep -vx 'README.md' || true)"
  if [[ -n "$otros" ]]; then
    echo "$destino ya tiene código ($(echo "$otros" | tr '\n' ' ')). No se sobrescribe." >&2
    exit 1
  fi
  if [[ -f "$destino/README.md" ]]; then
    readme_previo="$(grep -vx 'Pendiente de implementación\.' "$destino/README.md")"
  fi
fi

mkdir -p "$destino"
tar -C "$origen" \
  --exclude=.venv --exclude=__pycache__ --exclude=.pytest_cache \
  --exclude=.coverage --exclude=coverage.xml --exclude=junit.xml --exclude=.env \
  -cf - . | tar -C "$destino" -xf -

grep -rlI -e "$arquetipo" -e "$arquetipo_snake" "$destino" | while IFS= read -r archivo; do
  sed -i.bak "s/${arquetipo}/${nombre}/g; s/${arquetipo_snake}/${nombre_snake}/g" "$archivo"
  rm -f "${archivo}.bak"
done
find "$destino" -depth -name "*${arquetipo_snake}*" | while IFS= read -r ruta; do
  mv "$ruta" "$(dirname "$ruta")/$(basename "$ruta" | sed "s/${arquetipo_snake}/${nombre_snake}/g")"
done

desarrollo="$(sed -n "/^${marcador}\$/,\$p" "$destino/README.md" | tail -n +2)"
{
  if [[ -n "$readme_previo" ]]; then
    printf '%s\n' "$readme_previo"
  else
    printf '# %s\n' "$nombre"
  fi
  printf '%s\n' "$desarrollo"
} > "$destino/README.md"

cat <<EOF
Generado apps/backend/$nombre desde $arquetipo.

Siguientes pasos:
  1. Lee la HU en Jira (proyecto SOLV) y, si es BFF, la wiki Contratos-BFF / Backlog-BFF-web-movil.
  2. Reemplaza el agregado 'Ejemplo' por el del servicio (ver README del arquetipo).
EOF
if [[ "$tipo" == "ms" ]]; then
  echo "  3. Sustituye db/01_${nombre_snake}.sql por el DDL oficial db/schema/NN_${nombre_snake}.sql."
else
  echo "  3. Crea un cliente por microservicio en app/clients/ según la matriz canal → BFF → servicios."
fi
echo "  4. cd apps/backend/$nombre && pip install -e \".[test]\" && pytest -m \"not integration and not contract\" --cov"
