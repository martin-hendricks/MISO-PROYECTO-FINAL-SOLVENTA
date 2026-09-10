// ESCALONES de tasa de llegada (bloque 4), con el proveedor en un estado fijo.
//
// Cuatro escenarios `constant-arrival-rate` encadenados con `startTime` en vez
// de un `ramping-arrival-rate`. La diferencia importa: el ejecutor de rampa
// interpola la tasa entre los objetivos, asi que dentro de cada tramo la carga
// esta cambiando y el percentil del tramo mezcla varios niveles. Con escenarios
// discretos cada nivel es una meseta limpia y su percentil significa algo.
//
// El primer escenario arranca con un rodaje: la asignacion inicial de VUs de k6
// consume CPU en la misma caja que el sistema bajo prueba, y sin ese margen el
// transitorio contamina el primer escalon.
import http from 'k6/http';
import { check } from 'k6';
import { Trend } from 'k6/metrics';
import { elegirCliente } from './claves.js';

const dur = new Trend('ha01_cotizacion_duration', true);

const ESCALONES = (__ENV.ESCALONES || '20,50,100,200').split(',').map(Number);
const POR_ESCALON = Number(__ENV.ESCALON_S || 120);
const RODAJE = Number(__ENV.ESTABILIZACION_S || 60);

const scenarios = {};
ESCALONES.forEach((rate, i) => {
  scenarios['e' + rate] = {
    executor: 'constant-arrival-rate',
    rate: rate,
    timeUnit: '1s',
    duration: POR_ESCALON + 's',
    startTime: RODAJE + i * POR_ESCALON + 's',
    preAllocatedVUs: Math.max(200, rate * 2),
    maxVUs: Math.max(400, rate * 4),
    tags: { escalon: String(rate) },
  };
});

// Rodaje no contabilizado, a la tasa mas baja.
scenarios.rodaje = {
  executor: 'constant-arrival-rate',
  rate: ESCALONES[0],
  timeUnit: '1s',
  duration: RODAJE + 's',
  startTime: '0s',
  preAllocatedVUs: Math.max(200, ESCALONES[0] * 2),
  maxVUs: Math.max(400, ESCALONES[0] * 4),
  tags: { escalon: 'rodaje' },
};

export const options = {
  scenarios: scenarios,
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
    JSON.stringify({ customer_id: elegirCliente(), producto: 'VIAJE_BASICO' }),
    { headers: { 'Content-Type': 'application/json' }, timeout: '10s' }
  );
  dur.add(r.timings.duration);
  check(r, { 'status 200': (x) => x.status === 200 });
}
