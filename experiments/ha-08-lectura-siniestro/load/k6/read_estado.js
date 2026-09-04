import http from 'k6/http';
import { check } from 'k6';
import { Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://api:8000';
const ARM = __ENV.ARM || 'A';
const HOT_SET_SIZE = 10000;
const TOTAL = 1000000;
const HOT_RATIO = 0.8;

const latencia = new Trend('ha08_estado_duration', true);

export const options = {
  discardResponseBodies: false,
  scenarios: {
    escalones: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      preAllocatedVUs: 100,
      maxVUs: 400,
      stages: [
        { target: 10, duration: '1m' },   // warm-up — SE DESCARTA
        { target: 10, duration: '3m' },
        { target: 25, duration: '3m' },
        { target: 50, duration: '3m' },
        { target: 80, duration: '3m' },
      ],
    },
  },
  thresholds: {
    'http_req_failed': ['rate<0.01'],
    'ha08_estado_duration': ['p(95)<150'],
  },
  tags: { arm: ARM, run_id: __ENV.RUN_ID || 'r1' },
};

function pickId() {
  if (Math.random() < HOT_RATIO) {
    return 1 + Math.floor(Math.random() * HOT_SET_SIZE);
  }
  return 1 + Math.floor(Math.random() * TOTAL);
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
