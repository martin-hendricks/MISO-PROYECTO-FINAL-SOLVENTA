import { Given, Then, When } from '@cucumber/cucumber';
import { emptyHome } from '../support/data/generators';
import { PortalWorld } from '../support/world';

const FILA = {
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
  distanciaKm: 0.9,
};

const BUSQUEDA = {
  centro: { lat: 4.6432, lng: -74.0631, origen: 'posicion' },
  radioKm: 10,
  truncado: false,
  prestadores: [FILA],
};

function filaMx(id: string, nombre: string, ciudad: string) {
  return { ...FILA, id, nombre, ciudad, pais: 'MX', ramos: ['proteccion-dispositivo'], distanciaKm: null };
}

const CDMX = ['PRE-CDMX-01', 'PRE-CDMX-02', 'PRE-CDMX-03', 'PRE-CDMX-04', 'PRE-CDMX-05'];
const GDL = ['PRE-GDL-01', 'PRE-GDL-02', 'PRE-GDL-03', 'PRE-GDL-04'];

function busquedaMexico(query: URLSearchParams) {
  const ciudad = query.get('ciudad');
  const ids = query.get('pais') !== 'MX' ? [] : ciudad === 'Guadalajara' ? GDL : ciudad === 'Ciudad de México' ? CDMX : [];
  return {
    centro: null,
    radioKm: null,
    truncado: false,
    prestadores: ids.map((id) => filaMx(id, id, ciudad ?? '')),
  };
}

async function entrar(world: PortalWorld): Promise<void> {
  await world.bff.acceptSignIn(world.account.email, 'cliente');
  await world.bff.serveHome(emptyHome());
  await world.login.open('customer');
  await world.login.signIn(world.account);
  await world.page.waitForURL('**/inicio');
}

Given('providers near the customer', async function (this: PortalWorld) {
  await this.bff.serveCustomerPrestadores(BUSQUEDA);
  await entrar(this);
});

Given('providers in Mexico for a customer using es-MX', async function (this: PortalWorld) {
  await this.page.addInitScript(() => localStorage.setItem('solventa.locale', 'es-MX'));
  await this.bff.serveCustomerPrestadores(busquedaMexico);
  await entrar(this);
});

Given('a geotagged claim with providers', async function (this: PortalWorld) {
  await this.bff.serveClaimPrestadores('sin-1988', 200, {
    ...BUSQUEDA,
    centro: { lat: 4.626, lng: -74.15, origen: 'siniestro' },
    siniestro: { id: 'sin-1988', numero: 'SIN-1988', ramo: 'soat-motocicleta' },
    ramoFijo: 'soat-motocicleta',
    sinGeoetiqueta: false,
    prestadores: [{ ...FILA, distanciaKm: 0.8 }],
  });
  await entrar(this);
});

Given('a claim without a geotag', async function (this: PortalWorld) {
  await this.bff.serveClaimPrestadores('sin-vacio', 200, {
    ...BUSQUEDA,
    centro: null,
    siniestro: { id: 'sin-vacio', numero: 'SIN-2000', ramo: 'viaje' },
    ramoFijo: 'viaje',
    sinGeoetiqueta: true,
    prestadores: [],
  });
  await this.bff.serveCustomerPrestadores(BUSQUEDA);
  await entrar(this);
});

Given("another customer's claim", async function (this: PortalWorld) {
  await this.bff.serveClaimPrestadores('ajeno', 404, { detail: 'no_encontrado' });
  await entrar(this);
});

When('the customer opens providers near me', async function (this: PortalWorld) {
  await this.prestadores.openNearMe();
});

When('the customer opens providers without location', async function (this: PortalWorld) {
  await this.prestadores.openBlocked();
});

When('the customer picks the city {string}', async function (this: PortalWorld, ciudad: string) {
  await this.prestadores.pickCity(ciudad);
});

When('the customer opens providers for {string}', async function (this: PortalWorld, id: string) {
  await this.prestadores.openClaim(id);
});

When('the customer uses their location from the claim', async function (this: PortalWorld) {
  await this.prestadores.useMyLocation();
});

Then('the provider list shows the nearest workshop and its distance', async function (this: PortalWorld) {
  await this.prestadores.expectRow('PRE-BOG-06');
  await this.prestadores.expectDistance('PRE-BOG-06', /0,9/);
  await this.prestadores.openRow('PRE-BOG-06');
  await this.prestadores.expectDirections('PRE-BOG-06', 4.6355, -74.0655);
});

Then('the provider list has no distances and offers the cities', async function (this: PortalWorld) {
  await this.prestadores.expectRow('PRE-BOG-06');
  await this.prestadores.expectNoDistance('PRE-BOG-06');
  await this.prestadores.expectBlockedCities();
});

Then('the Mexican cities are offered with Ciudad de México marked', async function (this: PortalWorld) {
  await this.prestadores.expectCities(['ciudad-de-mexico', 'guadalajara', 'monterrey'], 'ciudad-de-mexico');
});

Then('the five Mexico City providers are listed without distances', async function (this: PortalWorld) {
  await this.prestadores.expectRows(CDMX);
  for (const id of CDMX) {
    await this.prestadores.expectNoDistance(id);
  }
});

Then('the four Guadalajara providers are listed', async function (this: PortalWorld) {
  await this.prestadores.expectRows(GDL);
  await this.prestadores.expectCities(['ciudad-de-mexico', 'guadalajara', 'monterrey'], 'guadalajara');
});

Then('the provider list is shown without a map', async function (this: PortalWorld) {
  await this.prestadores.expectListWithoutMap('PRE-BOG-06');
});

Then('the claim providers are fixed to the event', async function (this: PortalWorld) {
  await this.prestadores.expectClaimHeader('SIN-1988');
  await this.prestadores.expectDistance('PRE-BOG-06', /del evento/);
});

Then('the claim offers to use the customer location', async function (this: PortalWorld) {
  await this.prestadores.expectNoGeotag();
});

Then('the providers switch to near me', async function (this: PortalWorld) {
  await this.prestadores.expectNearMe();
  await this.prestadores.expectRow('PRE-BOG-06');
});

Then('the claim providers are not found', async function (this: PortalWorld) {
  await this.prestadores.expectNotFound();
});
