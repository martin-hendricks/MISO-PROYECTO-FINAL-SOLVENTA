#!/bin/sh
# Levanta todo el backend local (docker-compose.yml) y deja el esquema de
# cada microservicio al día, incluyendo migraciones que alguien agregue
# DESPUÉS de que el volumen de datos ya exista.
#
# Por qué existe: docker-entrypoint-initdb.d (los volúmenes montados en
# db-*.volumes de docker-compose.yml) solo corre una vez, cuando Postgres
# crea el volumen de datos desde cero. Si el volumen ya existe de una sesión
# anterior, un .sql nuevo que alguien agregue en apps/backend/<servicio>/db/
# nunca se aplica -- el servicio levanta pero sus queries fallan con
# "column ... does not exist" (visto en vivo: ms-cotizacion/asesor_id,
# ms-suscripcion/regla, ms-identidad/02_usuarios_cms.sql, los tres en
# migraciones agregadas después de que el volumen local ya existía).
#
# Este script lleva un registro (tabla schema_migrations, igual que el
# mecanismo real de infra/k8s/platform/run-migrations.sh) de qué archivo ya
# se aplicó a cada base, y corre SOLO los que falten -- así "docker compose
# up" + este script dejan el local al día sin tener que borrar volúmenes
# (`down -v`, lo que perdería todos los datos de prueba) cada vez que
# alguien agrega una migración nueva.
#
# La primera vez que corre contra un volumen ya existente (de antes de que
# este script existiera), los .sql que docker-entrypoint-initdb.d ya aplicó
# fallan con "already exists" -- el script detecta ese error puntual, los
# marca como aplicados sin reintentarlos, y sigue con el resto. Para un
# volumen nuevo (recién creado), initdb.d ya corrió todo, así que todas las
# migraciones se detectan como "already exists" y quedan registradas de una.
#
# Uso:
#   cd apps/backend && ./levantar-local.sh
#   ./levantar-local.sh --no-build   (si ya compilaste las imágenes y solo quieres migrar)
set -eu
cd "$(dirname "$0")"

BUILD_FLAG="--build"
if [ "${1:-}" = "--no-build" ]; then
    BUILD_FLAG=""
fi

# servicio:base-de-datos -- el nombre de la base (db-<base>) no siempre es
# igual al nombre del servicio (ver docker-compose.yml); se lista explícito
# en vez de derivarlo de "ms-<algo>" a ciegas.
SERVICIOS="
ms-cotizacion:db-cotizacion
ms-identidad:db-identidad
ms-pagos:db-pagos
ms-perfilamiento:db-perfilamiento
ms-polizas:db-polizas
ms-siniestros:db-siniestros
ms-suscripcion:db-suscripcion
"

echo "== docker compose up -d $BUILD_FLAG =="
# shellcheck disable=SC2086
docker compose up -d $BUILD_FLAG

echo ""
echo "== Esperando a que las bases estén healthy =="
for par in $SERVICIOS; do
    base="${par#*:}"
    until [ "$(docker compose ps -q "$base" | xargs -I{} docker inspect -f '{{.State.Health.Status}}' {} 2>/dev/null)" = "healthy" ]; do
        sleep 1
    done
done
echo "Todas las bases healthy."

echo ""
echo "== Aplicando migraciones pendientes =="
for par in $SERVICIOS; do
    servicio="${par%%:*}"
    base="${par#*:}"
    contenedor=$(docker compose ps -q "$base")
    carpeta="$servicio/db"

    if [ -z "$contenedor" ]; then
        echo "  [$servicio] contenedor de $base no encontrado, se omite"
        continue
    fi
    if [ ! -d "$carpeta" ]; then
        continue
    fi

    echo "-- $servicio ($base) --"
    docker exec -i "$contenedor" psql -U postgres -d solventa -v ON_ERROR_STOP=1 -q <<'SQL'
CREATE TABLE IF NOT EXISTS public.schema_migrations (
    filename    TEXT PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
SQL

    for archivo in $(ls "$carpeta"/*.sql 2>/dev/null | sort); do
        nombre=$(basename "$archivo")
        ya_aplicado=$(docker exec -i "$contenedor" psql -U postgres -d solventa -t -A \
            -c "SELECT 1 FROM public.schema_migrations WHERE filename = '${nombre}'")

        if [ "$ya_aplicado" = "1" ]; then
            echo "  SKIP  $nombre (ya registrado)"
            continue
        fi

        salida=$(docker exec -i "$contenedor" psql -U postgres -d solventa -v ON_ERROR_STOP=1 -q \
            < "$archivo" 2>&1) && resultado=0 || resultado=$?

        if [ "$resultado" -eq 0 ]; then
            echo "  APPLY $nombre"
        elif echo "$salida" | grep -qi "already exists"; then
            # Volumen preexistente: docker-entrypoint-initdb.d ya corrió este
            # archivo cuando el volumen se creó, antes de que existiera este
            # script. No se reintenta -- solo se registra como aplicado.
            echo "  MARK  $nombre (ya existía del initdb.d original)"
        else
            echo "  ERROR $nombre:"
            echo "$salida" | sed 's/^/    /'
            exit 1
        fi

        docker exec -i "$contenedor" psql -U postgres -d solventa -q \
            -c "INSERT INTO public.schema_migrations (filename) VALUES ('${nombre}') ON CONFLICT DO NOTHING;"
    done
done

echo ""
echo "== Reiniciando microservicios para que tomen el esquema al día =="
docker compose restart ms-cotizacion ms-identidad ms-pagos ms-perfilamiento ms-polizas ms-siniestros ms-suscripcion bff-web bff-movil api-socios

echo ""
echo "== Backend local listo =="
echo "  bff-web:    http://localhost:8000"
echo "  bff-movil:  http://localhost:8007"
echo "  api-socios: http://localhost:8006"
echo ""
echo "Frontend (en otra terminal):"
echo "  cd ../web && pnpm start   # http://localhost:4200 (proxy /web -> bff-web real)"
