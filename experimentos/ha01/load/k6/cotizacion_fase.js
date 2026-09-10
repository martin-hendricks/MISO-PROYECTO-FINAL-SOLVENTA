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
      //
      // El peor caso real es el bloque 2 con acierto 50 % y proveedor
      // degradado: la mitad de las peticiones esperan el timeout duro de
      // 700 ms, luego RATE*0.5*0.7 VUs ocupadas. A 200 sol/s son ~70, mas
      // las del camino caliente. RATE*2 cubre eso con holgura.
      preAllocatedVUs: Math.max(200, RATE * 2),
      // El techo se acota a 2x lo preasignado. Antes era RATE*10 (2000 a
      // 200 sol/s) y permitia una espiral: peticiones lentas al arrancar ->
      // k6 asigna mas VUs -> asignarlas consume CPU -> mas lentitud. Medido:
      // 913 VUs, event loop de la API al 100 % y p95 de 5 s durante los
      // primeros 12 s. Con el techo bajo, k6 descarta iteraciones en vez de
      // entrar en la espiral, y el descarte AHORA se comprueba.
      maxVUs: Math.max(400, RATE * 4),
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
