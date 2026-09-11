// Variante de alta carga de read_estado.js (protocolo formal, Anexo C del
// diseño): mismos escalones de 3 min pero extendidos a 150/300/600 req/s,
// para intentar localizar el punto de quiebre que el rango 10-80 req/s del
// protocolo formal no alcanzó (ver INFORME.md §2.4).
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

// Mismo mecanismo de tagging por escalón/calor que read_estado.js — sin
// esto el p95 sale agregado sobre 150/300/600 rps y no se puede ubicar en
// qué escalón (si alguno) aparece el punto de quiebre, que es el objetivo
// de esta corrida (feedback externo, 2026-09-11: se había omitido al
// derivar este script de read_estado.js).
const ESCALONES = [
  { hasta: 60, target: 10, nombre: 'warmup' },   // SE DESCARTA en el análisis
  { hasta: 240, target: 150, nombre: 'r150' },
  { hasta: 420, target: 300, nombre: 'r300' },
  { hasta: 600, target: 600, nombre: 'r600' },
];

export const options = {
  discardResponseBodies: false,
  scenarios: {
    escalones_alta_carga: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      preAllocatedVUs: 200,
      maxVUs: 1500,
      stages: ESCALONES.map((e, i) => ({
        target: e.target,
        duration: `${e.hasta - (i > 0 ? ESCALONES[i - 1].hasta : 0)}s`,
      })),
    },
  },
  thresholds: {
    'http_req_failed': ['rate<0.01'],
    'ha08_estado_duration': ['p(95)<150'],
    // Declarar thresholds por sub-métrica hace que k6 incluya cada una como
    // entrada separada en --summary-export (verificado con k6 run real), con
    // su propio p95 — así el p95 por escalón queda en el JSON directamente,
    // sin depender de reconstruirlo vía PromQL sobre el output
    // experimental-prometheus-rw (que expone gauges via TREND_STATS, no
    // buckets, así que histogram_quantile() sobre "_bucket" no aplica aquí
    // — feedback externo, 2026-09-11). El warm-up (nombre 'warmup') queda
    // fuera a propósito, igual que en el análisis.
    'ha08_estado_duration{escalon:r150}': ['p(95)<150'],
    'ha08_estado_duration{escalon:r300}': ['p(95)<150'],
    'ha08_estado_duration{escalon:r600}': ['p(95)<150'],
    'ha08_estado_duration{calor:caliente}': ['p(95)<150'],
    'ha08_estado_duration{calor:frio}': ['p(95)<150'],
  },
  tags: { arm: ARM, run_id: __ENV.RUN_ID || 'alta_carga' },
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
