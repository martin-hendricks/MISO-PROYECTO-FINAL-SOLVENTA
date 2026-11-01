import { Inicio } from './inicio.gateway';

/** Same aggregate the `bff-web` stub answers, plus an origination. For specs only. */
export const INICIO: Inicio = {
  ofertaVigente: {
    cotizacionId: 'COT-1042',
    ramo: 'Protección de dispositivo',
    estado: 'oferta_vigente',
  },
  poliza: {
    numero: 'POL-88219-CO',
    ramo: 'Protección de dispositivo',
    estado: 'vigente',
  },
  siniestroEnCurso: { siniestroId: 'SIN-441', estado: 'en_evaluacion' },
  hipotecario: { estado: 'disponible' },
};

export const INICIO_VACIO: Inicio = {
  ofertaVigente: null,
  poliza: null,
  siniestroEnCurso: null,
  hipotecario: null,
};
