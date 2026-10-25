#!/bin/sh
# Corre contra $database_url (inyectado vía envFrom desde el Secret de
# ExternalSecrets del servicio) cada archivo .sql montado en /migrations
# (junto con este propio script, en el mismo ConfigMap), en orden
# alfabético, saltando los que ya están registrados en public.schema_migrations.
#
# Los .sql de este repo (ver apps/backend/*/db/) no son idempotentes -- usan
# CREATE TABLE y CREATE INDEX sin IF NOT EXISTS -- así que no basta con
# "intentar y seguir si falla": hay que llevar un registro explícito de qué
# ya se aplicó y no reejecutarlo. schema_migrations vive en la misma base
# (DBCompartida o la que corresponda), fuera de cualquier esquema de
# microservicio, para que todos los servicios que migran contra la misma
# base compartan la misma tabla de control sin chocar entre sí.
set -eu

DB_URL=$(echo "$database_url" | sed 's/+asyncpg//')
DB_PASS=$(echo "$DB_URL" | sed -n 's#^[a-z]*://[^:]*:\([^@]*\)@.*#\1#p')
DB_PASS=$(printf '%b' "$(echo "$DB_PASS" | sed 's/%/\\x/g')")

psql "$DB_URL" -v ON_ERROR_STOP=1 -q <<'SQL'
CREATE TABLE IF NOT EXISTS public.schema_migrations (
    filename    TEXT PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
SQL

for archivo in $(ls /migrations/*.sql | sort); do
    nombre=$(basename "$archivo")
    ya_aplicado=$(psql "$DB_URL" -t -A -c \
        "SELECT 1 FROM public.schema_migrations WHERE filename = '${nombre}'")

    if [ "$ya_aplicado" = "1" ]; then
        echo "SKIP  ${nombre} (ya aplicado)"
        continue
    fi

    echo "APPLY ${nombre}"
    psql "$DB_URL" -v ON_ERROR_STOP=1 -v dbpass="$DB_PASS" -q -1 \
        -c "\i ${archivo}" \
        -c "INSERT INTO public.schema_migrations (filename) VALUES ('${nombre}')"
done

echo "Migraciones al día."
