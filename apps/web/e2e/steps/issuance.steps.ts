import assert from 'node:assert/strict';
import { Given, Then, When } from '@cucumber/cucumber';
import { clients } from '../support/data/generators';
import { PortalWorld } from '../support/world';

const SOLICITUD = 'COT-0091';
const CLIENTE = 'CLI-18';
const MOTIVO = 'La firma electrónica no fue exitosa: Firma rechazada por el firmante';

const pasos = (emision: string, poliza: string) => [
  { paso: 'COTIZAR', estado: 'COMPLETADO' },
  { paso: 'OFERTA', estado: 'COMPLETADO' },
  { paso: 'EMISION', estado: emision },
  { paso: 'POLIZA', estado: poliza },
];

// Shapes of POST /asesor/emisiones and POST /asesor/emisiones/{id}/poliza in bff-web.
const APROBADA = {
  solicitudId: SOLICITUD,
  cliente: { clienteId: CLIENTE, nombre: 'Andrés Gómez' },
  producto: 'Protección de dispositivo',
  referencia: SOLICITUD,
  pasos: pasos('ACTUAL', 'PENDIENTE'),
  decision: {
    resultado: 'ACEPTADA',
    regla: 'Score de riesgo hasta 0.7000',
    detalle: 'Riesgo dentro del apetito de la aseguradora',
    decididoPor: 'Motor automático',
    decididoEn: '2026-10-28T15:24:00Z',
  },
  oferta: { moneda: 'COP', primaTotal: 106900, primaNeta: 97900, expedicion: 9000, vigenciaMeses: 12 },
};

const FIRMA_FALLIDA = { resultado: 'RECHAZADA', motivo: MOTIVO, pasos: pasos('ERROR', 'PENDIENTE') };

Given('an asesor on an offer the core approved', async function (this: PortalWorld) {
  this.clientes = clients(5);
  await this.bff.serveClients(this.clientes);
  await this.bff.serveAdvisorIssuance(APROBADA, FIRMA_FALLIDA);
  await this.bff.acceptSignIn(this.account.email, 'asesor');
  await this.login.open('backoffice');
  await this.login.signIn(this.account);
  await this.backoffice.waitForShell();
  await this.page.goto(`/cms/cotizaciones/${SOLICITUD}/emision?cliente=${CLIENTE}`);
  await this.page.getByTestId('emitir').waitFor({ state: 'visible' });
});

When(
  'the asesor issues it and the electronic signature fails',
  async function (this: PortalWorld) {
    await this.page.getByTestId('emitir').click();
    await this.page.getByTestId('rechazo').waitFor({ state: 'visible' });
    assert.equal(this.bff.issuesRequested(), 1);
  },
);

Then('the Emisión step of the stepper is marked as an error', async function (this: PortalWorld) {
  const step = this.page.getByTestId('stepper').locator('[data-paso="EMISION"]');
  assert.equal(await step.getAttribute('data-estado'), 'ERROR');
});

Then('the asesor sees the reason the signature failed', async function (this: PortalWorld) {
  assert.equal((await this.page.getByTestId('rechazo-motivo').textContent())?.trim(), MOTIVO);
});

Then('no policy is shown as issued', async function (this: PortalWorld) {
  assert.equal(await this.page.getByTestId('poliza-emitida').count(), 0);
  assert.equal(await this.page.getByTestId('emitir').count(), 0);
});

Then(
  'the asesor can quote another product for the same customer',
  async function (this: PortalWorld) {
    const href = await this.page.getByTestId('cotizar-otro').getAttribute('href');
    assert.equal(href, `/cms/cotizaciones?cliente=${CLIENTE}`);
  },
);
