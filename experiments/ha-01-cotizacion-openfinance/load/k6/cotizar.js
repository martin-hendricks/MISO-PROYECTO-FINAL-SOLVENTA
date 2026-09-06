import http from 'k6/http';
import { check } from 'k6';
import { Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://api:8000';
const ARM = __ENV.ARM || 'A';
const TOTAL_CLIENTES = 100000;

const latencia = new Trend('ha01_cotizacion_duration', true);

export const options = {
  discardResponseBodies: false,
  scenarios: {
    trafico_alto: {
      executor: 'ramping-arrival-rate',
      startRate: 20,
      timeUnit: '1s',
      preAllocatedVUs: 100,
      maxVUs: 300,
      stages: [
        { target: 20, duration: '30s' },   // warm-up — SE DESCARTA
        { target: 200, duration: '3m' },
      ],
    },
  },
  thresholds: {
    'http_req_failed': ['rate<0.01'],
    // Umbral medido en el servicio (sin el salto del ApiGateway),
    // según el Anexo B del diseño del experimento HA-01.
    'ha01_cotizacion_duration': ['p(95)<225', 'p(99)<475'],
  },
  tags: { arm: ARM, run_id: __ENV.RUN_ID || 'r1' },
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
  check(res, {
    'status 200': (r) => r.status === 200,
    'tiene prima': (r) => r.json('prima') !== undefined,
  });
}
