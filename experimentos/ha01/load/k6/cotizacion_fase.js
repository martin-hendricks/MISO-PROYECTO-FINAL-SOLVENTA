// Corridas por FASES (bloques 1 y 3): tasa de llegada constante mientras el
// estado del proveedor se conmuta en caliente.
//
// Sin threshold de latencia: durante la fase degradada se ESPERA una
// diferencia, y el criterio se evalua por fase en el analisis, no aqui.
// Un threshold global abortaria la corrida justo en la fase que interesa.
import http from 'k6/http';
import { check } from 'k6';
import { Trend, Rate } from 'k6/metrics';
import { elegirCliente } from './claves.js';

const dur = new Trend('ha01_cotizacion_duration', true);
const degradadas = new Rate('ha01_respuesta_degradada');

const RATE = Number(__ENV.RATE || 100);
const DURATION = __ENV.DURATION || '5m';
const PRODUCTO = __ENV.PRODUCTO || 'VIAJE_BASICO';

export const options = {
  scenarios: {
    fase: {
      executor: 'constant-arrival-rate',
      rate: RATE,
      timeUnit: '1s',
      duration: DURATION,
      // Holgado a proposito: si k6 se queda sin VUs deja de emitir a la tasa
      // fijada y la carga cae sola, que es exactamente el sesgo que el
      // ejecutor de tasa de llegada existe para evitar.
      preAllocatedVUs: Math.max(100, RATE * 2),
      maxVUs: Math.max(400, RATE * 10),
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.05'],
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
    JSON.stringify({ customer_id: elegirCliente(), producto: PRODUCTO }),
    { headers: { 'Content-Type': 'application/json' }, timeout: '10s' }
  );
  dur.add(r.timings.duration);
  const ok = check(r, { 'status 200': (x) => x.status === 200 });
  if (ok) {
    try {
      degradadas.add(r.json('degradada') === true);
    } catch (e) {
      degradadas.add(false);
    }
  }
}
