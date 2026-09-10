// Escalones de tasa de llegada (20/50/100/200 sol/s) con el proveedor en un
// estado fijo. Aqui SI se codifica el criterio de aceptacion como threshold.
import http from 'k6/http';
import { check } from 'k6';
import { Trend } from 'k6/metrics';
import { elegirCliente } from './claves.js';

const dur = new Trend('ha01_cotizacion_duration', true);

const P95 = Number(__ENV.SLO_P95_MS || 225);
const P99 = Number(__ENV.SLO_P99_MS || 475);

export const options = {
  scenarios: {
    escalones: {
      executor: 'ramping-arrival-rate',
      startRate: 20,
      timeUnit: '1s',
      preAllocatedVUs: 300,
      maxVUs: 2000,
      stages: [
        { target: 20, duration: '2m' },
        { target: 50, duration: '2m' },
        { target: 100, duration: '2m' },
        { target: 200, duration: '2m' },
      ],
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    // 225 / 475 ms EN EL SERVICIO = 250 / 500 ms extremo a extremo menos el
    // presupuesto de borde del Anexo G. NO son 250/500: si aparece 250 en un
    // threshold, se esta midiendo contra el umbral equivocado.
    ha01_cotizacion_duration: [`p(95)<${P95}`, `p(99)<${P99}`],
  },
  tags: {
    arm: __ENV.ARM || 'na',
    state: __ENV.PROVIDER_STATE || 'na',
    hit: __ENV.TARGET_HIT_RATE || 'na',
    run: __ENV.RUN_ID || 'na',
  },
};

export default function () {
  const r = http.post(
    'http://api:8000/v1/cotizaciones',
    JSON.stringify({ customer_id: elegirCliente(), producto: 'VIAJE_BASICO' }),
    { headers: { 'Content-Type': 'application/json' }, timeout: '10s' }
  );
  dur.add(r.timings.duration);
  check(r, { 'status 200': (x) => x.status === 200 });
}
