// Seleccion de claves con TRES POOLS DISJUNTOS.
//
// Ajuste al Anexo A del documento de diseno. La precarga original dejaba
// ausente el (1 - acierto) del universo, pero cada fallo REPUEBLA la cache:
// con el proveedor sano la fraccion ausente se consume durante la corrida y
// la tasa de acierto observada SUBE. La tasa de acierto es la variable
// independiente del bloque 2, asi que no puede derivar mientras se mide.
//
//   CALIENTE  cli_h*  precargado fresco        -> acierto de cache
//   VENCIDO   cli_s*  precargado con edad>TTL  -> fallo, resuelve a `fallback`
//   FRIO      cli_c*  nunca precargado         -> fallo, resuelve a `default`
//
// Los pools de fallo son mucho mayores que el numero de fallos de una
// corrida (a 100 sol/s y 4 % de fallo son ~1400 claves sobre 100 000), asi
// que la probabilidad de volver a sortear una clave ya repoblada queda por
// debajo del 1 % y dentro de la tolerancia de +-2 puntos de verify_hitrate.
//
// El pool VENCIDO existe porque los dos caminos de degradacion no son el
// mismo: sin valor previo el brazo C tarifica con el perfil por defecto y
// nunca ejercitaria el "ultimo valor conocido", que es la mitad de la
// tactica bajo prueba.

export const N_HOT = Number(__ENV.UNIVERSO_CLIENTES || 50000);
export const N_STALE = Number(__ENV.POOL_STALE || 100000);
// Se conserva por compatibilidad; el pool frio ya no lo usa.
export const N_COLD = Number(__ENV.POOL_COLD || 100000);
export const HIT_RATE = Number(__ENV.TARGET_HIT_RATE || 0.96);
export const STALE_FRACTION = Number(__ENV.MISS_STALE_FRACTION || 0.5);

function pad(n) {
  return String(n).padStart(6, '0');
}

export function elegirCliente() {
  if (Math.random() < HIT_RATE) {
    return `cli_h${pad(Math.floor(Math.random() * N_HOT))}`;
  }
  if (Math.random() < STALE_FRACTION) {
    return `cli_s${pad(Math.floor(Math.random() * N_STALE))}`;
  }
  // El pool FRIO no es finito. Una clave fria repoblada por un refresco
  // exitoso pasaria a ser un acierto si volviera a salir sorteada, y eso
  // hace derivar la tasa de acierto. Con un espacio de 10^12 ids la
  // probabilidad de repetir una clave dentro de una corrida es nula, asi
  // que el pool frio aporta CERO deriva.
  //
  // El pool VENCIDO no puede hacer lo mismo: necesita un valor previo
  // realmente precargado, luego es finito por fuerza y su tamano se
  // dimensiona en warm_cache.py a partir de la deriva admisible.
  const a = Math.floor(Math.random() * 1e6);
  const b = Math.floor(Math.random() * 1e6);
  return `cli_c${pad(a)}${pad(b)}`;
}
