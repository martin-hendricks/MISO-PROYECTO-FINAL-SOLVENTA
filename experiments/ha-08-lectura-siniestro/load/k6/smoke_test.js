// Prueba de humo breve: NO es el protocolo formal (read_estado.js).
// Solo confirma que el pipeline k6 -> API -> Prometheus remote-write
// funciona antes de comprometer tiempo en las 9 corridas contrabalanceadas.
import http from 'k6/http';
import { check } from 'k6';
import { Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://api:8000';
const ARM = __ENV.ARM || 'A';
const HOT_SET_SIZE = 10000;

const latencia = new Trend('ha08_estado_duration', true);

export const options = {
  scenarios: {
    smoke: {
      executor: 'constant-arrival-rate',
      rate: 10,
      timeUnit: '1s',
      duration: '20s',
      preAllocatedVUs: 20,
      maxVUs: 50,
    },
  },
  tags: { arm: ARM, run_id: 'smoke' },
};

function pickId() {
  return 1 + Math.floor(Math.random() * HOT_SET_SIZE);
}

export default function () {
  const id = pickId();
  const res = http.get(`${BASE_URL}/siniestros/${id}/estado`, {
    tags: { name: 'GET /siniestros/{id}/estado' },
  });
  latencia.add(res.timings.duration);
  check(res, {
    'status 200': (r) => r.status === 200,
    'tiene estado': (r) => r.json('estado') !== undefined,
  });
}
