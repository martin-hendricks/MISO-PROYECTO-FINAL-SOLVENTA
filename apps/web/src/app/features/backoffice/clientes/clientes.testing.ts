import { Cliente } from './clientes.gateway';

/** Same portfolio the `bff-web` stub answers. For specs only. */
export const CLIENTES: Cliente[] = [
  {
    clienteId: 'CLI-18',
    nombre: 'Andrés Gómez',
    documento: '1020334556',
    canal: 'web',
    estado: 'activo',
    consentimiento: 'habeas_data',
  },
  {
    clienteId: 'CLI-19',
    nombre: 'Laura Peña',
    documento: '52448901',
    canal: 'android',
    estado: 'activo',
    consentimiento: 'habeas_data',
  },
  {
    clienteId: 'CLI-20',
    nombre: 'Ricardo Salas',
    documento: '80112334',
    canal: 'web',
    estado: 'activo',
    consentimiento: 'hipotecario_pendiente',
  },
  {
    clienteId: 'CLI-21',
    nombre: 'Marcela Ruiz',
    documento: '41778220',
    canal: 'android',
    estado: 'activo',
    consentimiento: 'habeas_data',
  },
  {
    clienteId: 'CLI-22',
    nombre: 'Julián Torres',
    documento: '79330114',
    canal: 'web',
    estado: 'inactivo',
    consentimiento: 'revocado',
  },
];
