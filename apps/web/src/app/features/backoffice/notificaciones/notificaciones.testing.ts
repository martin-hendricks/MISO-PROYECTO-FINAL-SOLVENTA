import { UsuarioAudiencia, DifusionItem, DifusionResultado } from './notificaciones.gateway';

export const AUDIENCIA: UsuarioAudiencia[] = [
  {
    usuarioId: '11111111-1111-4111-8111-111111111111',
    nombre: 'Ana',
    apellidos: 'Ruiz',
    email: 'ana@correo.com',
    documento: '1020334556',
    dispositivosActivos: 1,
  },
  {
    usuarioId: '22222222-2222-4222-8222-222222222222',
    nombre: 'Luis',
    apellidos: 'Paz',
    email: 'luis@correo.com',
    documento: '52448901',
    dispositivosActivos: 2,
  },
];

export const RESULTADO: DifusionResultado = {
  difusionId: 'c2d40000-0000-4000-8000-000000000001',
  enviadas: 2,
  fallidas: 1,
  sinDispositivo: 0,
};

export const HISTORIAL: DifusionItem[] = [
  {
    ...RESULTADO,
    titulo: 'Mantenimiento',
    cuerpo: 'La app no estará disponible.',
    poliza: null,
    creadaEn: '2026-11-09T13:05:00Z',
  },
];
