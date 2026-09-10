import http from 'k6/http';
import { check } from 'k6';
import { Trend } from 'k6/metrics';
import exec from 'k6/execution';

const BASE_URL = __ENV.BASE_URL || 'http://api:8000';
const ARM = __ENV.ARM || 'A';
const HOT_SET_SIZE = 10000;
const TOTAL = 1000000;
const HOT_RATIO = 0.8;

const latencia = new Trend('ha08_estado_duration', true);

// Límites acumulados (segundos desde el inicio del escenario) de cada etapa,
// para poder taggear cada request con su escalón real y así recuperar el
// p95 por escalón desde Prometheus (punto de sensibilidad 3 del diseño) en
// vez de un único p95 agregado de toda la corrida — ver
// EVALUACION_EJECUCION_HA-08.md §3.1.
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
    return { id: 1 + Math.floor(Math.random() * HOT_SET_SIZE), calor: 'caliente' };
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
