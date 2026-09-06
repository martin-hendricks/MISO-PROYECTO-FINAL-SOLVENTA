// Variante de tráfico bajo (10 sol/s) para el punto de sensibilidad 4:
// verifica si el umbral por conteo del interruptor mantiene las peticiones
// sacrificadas bajo el 1% incluso cuando el conteo tarda más en llenarse.
import http from 'k6/http';
import { check } from 'k6';
import { Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://api:8000';
const ARM = __ENV.ARM || 'C';
const TOTAL_CLIENTES = 100000;

const latencia = new Trend('ha01_cotizacion_duration', true);

export const options = {
  scenarios: {
    trafico_bajo: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      preAllocatedVUs: 30,
      maxVUs: 60,
      stages: [
        { target: 10, duration: '3m' },
      ],
    },
  },
  thresholds: {
    'http_req_failed': ['rate<0.01'],
  },
  tags: { arm: ARM, run_id: __ENV.RUN_ID || 'r1', traffic: 'low' },
};

function pickClienteId() {
  return 1 + Math.floor(Math.random() * TOTAL_CLIENTES);
}

export default function () {
  const id = pickClienteId();
  const res = http.get(`${BASE_URL}/cotizaciones/${id}`, {
    tags: { name: 'GET /cotizaciones/{id}' },
  });
  latencia.add(res.timings.duration);
  check(res, { 'status 200': (r) => r.status === 200 });
}
