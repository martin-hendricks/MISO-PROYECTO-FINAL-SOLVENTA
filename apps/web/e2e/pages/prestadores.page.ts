import assert from 'node:assert/strict';
import { Page } from 'playwright';

export class PrestadoresPage {
  constructor(private readonly page: Page) {}

  async openNearMe(): Promise<void> {
    await this.page.context().grantPermissions(['geolocation']);
    await this.page.context().setGeolocation({ latitude: 4.6355, longitude: -74.0655 });
    await this.open('/siniestros/prestadores');
  }

  async openBlocked(): Promise<void> {
    await this.page.context().clearPermissions();
    await this.open('/siniestros/prestadores');
  }

  async openClaim(id: string): Promise<void> {
    await this.open(`/siniestros/${id}/prestadores`);
  }

  async open(path: string): Promise<void> {
    await this.page.goto(path);
    await this.page.getByTestId('prestadores').waitFor({ state: 'visible' });
  }

  async expectRow(id: string): Promise<void> {
    await this.page.getByTestId(`fila-prestador-${id}`).waitFor({ state: 'visible' });
  }

  async expectDistance(id: string, pattern: RegExp): Promise<void> {
    const distancia = this.page.getByTestId(`distancia-${id}`);
    await distancia.waitFor({ state: 'visible' });
    assert.match((await distancia.textContent()) ?? '', pattern);
  }

  async expectNoDistance(id: string): Promise<void> {
    assert.equal(await this.page.getByTestId(`distancia-${id}`).count(), 0);
  }

  async expectBlockedCities(): Promise<void> {
    await this.page.getByTestId('prestadores-bloqueado').waitFor({ state: 'visible' });
    await this.page.getByTestId('chip-ciudad-bogota').waitFor({ state: 'visible' });
    await this.page.getByTestId('chip-ciudad-medellin').waitFor({ state: 'visible' });
    await this.page.getByTestId('chip-ciudad-chia').waitFor({ state: 'visible' });
    assert.equal(await this.page.getByTestId('prestadores').getAttribute('data-mode'), 'chooseCity');
  }

  async expectListWithoutMap(id: string): Promise<void> {
    await this.expectRow(id);
    assert.equal(await this.page.getByTestId('prestadores-mapa').count(), 0);
  }

  async openRow(id: string): Promise<void> {
    await this.page.getByTestId(`fila-prestador-${id}`).click();
    await this.page.getByTestId(`detalle-${id}`).waitFor({ state: 'visible' });
  }

  async expectDirections(id: string, lat: number, lng: number): Promise<void> {
    const link = this.page.getByTestId(`como-llegar-${id}`);
    await link.waitFor({ state: 'visible' });
    assert.equal(await link.getAttribute('href'), `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`);
    assert.equal(await link.getAttribute('target'), '_blank');
  }

  async expectClaimHeader(numero: string): Promise<void> {
    const titulo = this.page.getByTestId('prestadores-titulo');
    await titulo.waitFor({ state: 'visible' });
    assert.match((await titulo.textContent()) ?? '', new RegExp(numero));
    assert.equal(await this.page.getByTestId('prestadores').getAttribute('data-mode'), 'claim');
  }

  async expectNoGeotag(): Promise<void> {
    await this.page.getByTestId('prestadores-sin-geo').waitFor({ state: 'visible' });
    await this.page.getByTestId('usar-ubicacion').waitFor({ state: 'visible' });
  }

  async useMyLocation(): Promise<void> {
    await this.page.context().grantPermissions(['geolocation']);
    await this.page.context().setGeolocation({ latitude: 4.6355, longitude: -74.0655 });
    await this.page.getByTestId('usar-ubicacion').click();
  }

  async expectNearMe(): Promise<void> {
    await this.page.getByTestId('prestadores').waitFor({ state: 'visible' });
    assert.equal(await this.page.getByTestId('prestadores').getAttribute('data-mode'), 'nearMe');
  }

  async expectNotFound(): Promise<void> {
    await this.page.getByTestId('prestadores-not-found').waitFor({ state: 'visible' });
  }
}
