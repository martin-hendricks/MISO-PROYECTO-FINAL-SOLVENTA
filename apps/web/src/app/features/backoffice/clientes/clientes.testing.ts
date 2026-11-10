import { Cliente } from './clientes.gateway';

export const CLIENTES: Cliente[] = [
  {
    usuarioId: '11111111-1111-4111-8111-111111111111',
    nombre: 'Andrés',
    apellidos: 'Gómez',
    email: 'andres@correo.com',
    documento: '1020334556',
    estado: 'ACTIVO',
    dispositivosActivos: 1,
  },
  {
    usuarioId: '22222222-2222-4222-8222-222222222222',
    nombre: 'Laura',
    apellidos: 'Peña',
    email: 'laura@correo.com',
    documento: '52448901',
    estado: 'ACTIVO',
    dispositivosActivos: 0,
  },
  {
    usuarioId: '33333333-3333-4333-8333-333333333333',
    nombre: 'Ricardo',
    apellidos: 'Salas',
    email: 'ricardo@correo.com',
    documento: '80112334',
    estado: 'INACTIVO',
    dispositivosActivos: null,
  },
];

export const PAGINA = { clientes: CLIENTES, pagina: 1, hayMas: false };
