import { Given, Then, When } from '@cucumber/cucumber';
import { PortalWorld } from '../support/world';

const CONTEOS = { Bogotá: 30, Medellín: 20, Chía: 10 };

const TALLER = {
  id: 'PRE-BOG-06',
  nombre: 'Taller Moto Chapinero',
  tipo: 'taller-motos',
  ramos: ['soat-motocicleta'],
  direccion: 'Cra 13 #45-18',
  ciudad: 'Bogotá',
  barrio: 'Chapinero',
  lat: 4.6355,
  lng: -74.0655,
  telefono: '601 555 0112',
  horario: 'Lun–Sáb 7:00–19:00',
  estado: 'activo' as const,
  actualizadoEn: '2026-11-17T12:00:00Z',
};

Given('the operator catalog lists the Chapinero workshop', async function (this: PortalWorld) {
  await this.bff.serveOperadorPrestadores([TALLER], CONTEOS);
});

When('the operator opens the provider catalog', async function (this: PortalWorld) {
  await this.boPrestadores.open();
});

When('the operator creates, edits, deactivates and reactivates a provider', async function (this: PortalWorld) {
  await this.boPrestadores.create('Taller Moto Norte Usaquén');
  await this.boPrestadores.expectName('Taller Moto Norte Usaquén');
  await this.boPrestadores.editName('Taller Moto Norte');
  await this.boPrestadores.deactivate('PRE-E2E-01');
  await this.boPrestadores.reactivate('PRE-E2E-01');
});

When('the operator filters providers in Chía for climate and flights', async function (this: PortalWorld) {
  await this.boPrestadores.filterEmpty();
});

When('the operator clears the provider filters', async function (this: PortalWorld) {
  await this.boPrestadores.clearFilters();
});

Then('the provider catalog shows the city counts', async function (this: PortalWorld) {
  await this.boPrestadores.expectCounts(/Bogotá 30/);
  await this.boPrestadores.expectCounts(/Medellín 20/);
  await this.boPrestadores.expectCounts(/Chía 10/);
  await this.boPrestadores.expectRow('PRE-BOG-06');
});

Then('the provider is active again', async function (this: PortalWorld) {
  await this.boPrestadores.expectRow('PRE-E2E-01');
});

Then('the provider catalog explains the empty filter', async function (this: PortalWorld) {
  await this.boPrestadores.expectEmpty();
});

Then('the advisor cannot create or deactivate a provider', async function (this: PortalWorld) {
  await this.boPrestadores.expectNoCreateOrDeactivate();
  await this.boPrestadores.expectRow('PRE-BOG-06');
});
