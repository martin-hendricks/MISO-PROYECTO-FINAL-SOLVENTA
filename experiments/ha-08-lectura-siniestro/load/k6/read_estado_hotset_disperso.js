// Variante de read_estado.js para validar el hallazgo V1/V3/V6 de
// AUDITORIA_EXTERNA_HA-08.md: el p95 del brazo A podría ser artificialmente
// bajo porque (a) el dataset cabe en el caché de página del contenedor
// Postgres (2GB de límite, 3GB de dataset, pero el hot set consultado real
// es mucho menor) y (b) el hot set (IDs 1-10000) es físicamente contiguo —
// son las primeras filas insertadas por generate_series en 03_seed.sql, así
// que ocupan páginas consecutivas en el heap y los índices.
//
// Esta variante dispersa el hot set: en vez de IDs 1-10000 consecutivos,
// usa múltiplos de 100 en el rango 1-1.000.000 (10.000 valores distintos,
// mismo tamaño de hot set, pero distribuidos por todo el heap en vez de
// concentrados al principio). Solo cambia pickId() — el resto del protocolo
// (escalones, thresholds, tags) es idéntico a read_estado.js.
import http from 'k6/http';
import { check } from 'k6';
import { Trend } from 'k6/metrics';
import exec from 'k6/execution';

const BASE_URL = __ENV.BASE_URL || 'http://api:8000';
const ARM = __ENV.ARM || 'A';
const HOT_SET_SIZE = 10000;
const TOTAL = 1000000;
const HOT_RATIO = 0.8;
const HOT_SET_STRIDE = TOTAL / HOT_SET_SIZE; // 100

const latencia = new Trend('ha08_estado_duration', true);

const ESCALONES = [
  { hasta: 60, target: 10, nombre: 'warmup' },   // SE DESCARTA en el análisis
  { hasta: 240, target: 10, nombre: 'r10' },
  { hasta: 420, target: 25, nombre: 'r25' },
  { hasta: 600, target: 50, nombre: 'r50' },
  { hasta: 780, target: 80, nombre: 'r80' },
];

export const options = {
  discardResponseBodies: false,
  scenarios: {
    escalones: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      preAllocatedVUs: 100,
      maxVUs: 400,
      stages: ESCALONES.map((e, i) => ({
        target: e.target,
        duration: `${e.hasta - (i > 0 ? ESCALONES[i - 1].hasta : 0)}s`,
      })),
    },
  },
  thresholds: {
    'http_req_failed': ['rate<0.01'],
    'ha08_estado_duration': ['p(95)<150'],
  },
  tags: { arm: ARM, run_id: __ENV.RUN_ID || 'r1' },
};

function nombreEscalon(tSegundos) {
  for (const e of ESCALONES) {
    if (tSegundos <= e.hasta) return e.nombre;
  }
  return ESCALONES[ESCALONES.length - 1].nombre;
}

function pickId() {
  if (Math.random() < HOT_RATIO) {
    // Hot set disperso: múltiplos de HOT_SET_STRIDE (100) en vez de
    // 1..HOT_SET_SIZE consecutivos — mismo tamaño (10.000 claves), pero
    // distribuidas por todo el rango 1..TOTAL en vez de concentradas al
    // inicio (donde son físicamente contiguas en el heap de Postgres).
    const indice = Math.floor(Math.random() * HOT_SET_SIZE);
    return { id: 1 + indice * HOT_SET_STRIDE, calor: 'caliente' };
  }
  return { id: 1 + Math.floor(Math.random() * TOTAL), calor: 'frio' };
}

export default function () {
  const { id, calor } = pickId();
  const tSegundos = (Date.now() - exec.scenario.startTime) / 1000;
  const escalon = nombreEscalon(tSegundos);
  const res = http.get(`${BASE_URL}/siniestros/${id}/estado`, {
    tags: { name: 'GET /siniestros/{id}/estado', escalon, calor },
  });
  latencia.add(res.timings.duration, { escalon, calor });
  check(res, {
    'status 200': (r) => r.status === 200,
    'tiene estado': (r) => r.json('estado') !== undefined,
  });
}
