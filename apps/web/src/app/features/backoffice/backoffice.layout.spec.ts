import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { of, throwError } from 'rxjs';
import { provideSolventaI18n } from '../../core/i18n/provide-i18n';
import { Role } from '../../core/session/session.service';
import { BackofficeLayout } from './backoffice.layout';
import { sessionAs } from './backoffice.testing';
import { PerfilBackofficeGateway } from './perfil-backoffice.gateway';

@Component({ template: '<p data-testid="content">contenido</p>' })
class Content {}

describe('BackofficeLayout', () => {
  async function open(role: Role, url: string) {
    const session = sessionAs(role);
    TestBed.configureTestingModule({
      providers: [
        provideRouter([
          { path: 'cms/login', component: Content },
          {
            path: 'cms',
            component: BackofficeLayout,
            children: [
              { path: 'clientes', component: Content },
              { path: 'avisos', component: Content },
            ],
          },
        ]),
        ...provideSolventaI18n(),
        session.provider,
        { provide: PerfilBackofficeGateway, useValue: { load: () => of(null) } },
      ],
    });
    const harness = await RouterTestingHarness.create(url);
    const host = harness.routeNativeElement as HTMLElement;
    const element = (testId: string) =>
      host.querySelector<HTMLElement>(`[data-testid="${testId}"]`);
    return { harness, host, element, signOuts: session.signOuts };
  }

  it('shows Notificaciones only to the operator', async () => {
    const advisor = await open('asesor', '/cms/clientes');
    expect(advisor.element('nav-notificaciones')).toBeNull();

    TestBed.resetTestingModule();
    const operator = await open('operador', '/cms/avisos');
    expect(operator.element('nav-notificaciones')?.textContent).toContain('Notificaciones');
  });

  it('shows the Back-office tag and exactly six destinations', async () => {
    const { host, element } = await open('asesor', '/cms/clientes');

    const links = Array.from(host.querySelectorAll('nav a')).map((link) =>
      link.textContent?.trim(),
    );
    expect(element('backoffice-tag')?.textContent).toContain('Back-office');
    expect(links).toEqual([
      'Clientes',
      'Cotizaciones',
      'Pólizas',
      'Avisos',
      'Reportes',
      'Métricas',
    ]);
  });

  it('marks only the current destination', async () => {
    const { host, element } = await open('asesor', '/cms/avisos');

    expect(element('nav-avisos')?.getAttribute('aria-current')).toBe('page');
    expect(host.querySelectorAll('nav a.active').length).toBe(1);
  });

  it('shows the role of the session as read-only text', async () => {
    const { element } = await open('operador', '/cms/avisos');

    expect(element('role-selector')?.textContent).toContain('Operador');
    expect(element('role-selector')?.querySelector('select, button')).toBeNull();
  });

  it('keeps the shell around the section content', async () => {
    const { element } = await open('asesor', '/cms/clientes');

    expect(element('top-nav-admin')).not.toBeNull();
    expect(element('content')).not.toBeNull();
  });

  it('shows the initials of the logged-in asesor/operador next to sign out', async () => {
    const session = sessionAs('operador');
    TestBed.configureTestingModule({
      providers: [
        provideRouter([
          {
            path: 'cms',
            component: BackofficeLayout,
            children: [{ path: 'clientes', component: Content }],
          },
        ]),
        ...provideSolventaI18n(),
        session.provider,
        {
          provide: PerfilBackofficeGateway,
          useValue: {
            load: () =>
              of({ usuarioId: 'u1', correo: 'jorge@solventa.co', nombre: 'Jorge', apellidos: 'Nieto', rol: 'operador' }),
          },
        },
      ],
    });
    const harness = await RouterTestingHarness.create('/cms/clientes');
    harness.fixture.detectChanges();
    await harness.fixture.whenStable();
    harness.fixture.detectChanges();
    const host = harness.routeNativeElement as HTMLElement;

    const avatar = host.querySelector('[data-testid="avatar"]');
    expect(avatar?.textContent?.trim()).toBe('JN');
    expect(avatar?.getAttribute('title')).toBe('Jorge Nieto');
  });

  it('leaves the avatar empty if the profile fails to load, without crashing', async () => {
    const session = sessionAs('asesor');
    TestBed.configureTestingModule({
      providers: [
        provideRouter([
          {
            path: 'cms',
            component: BackofficeLayout,
            children: [{ path: 'clientes', component: Content }],
          },
        ]),
        ...provideSolventaI18n(),
        session.provider,
        { provide: PerfilBackofficeGateway, useValue: { load: () => throwError(() => new Error('caida')) } },
      ],
    });
    const harness = await RouterTestingHarness.create('/cms/clientes');
    harness.fixture.detectChanges();
    await harness.fixture.whenStable();
    harness.fixture.detectChanges();
    const host = harness.routeNativeElement as HTMLElement;

    const avatar = host.querySelector('[data-testid="avatar"]');
    expect(avatar?.textContent?.trim()).toBe('');
  });

  it('closes the session and returns to the back-office login', async () => {
    const { harness, element, signOuts } = await open('asesor', '/cms/clientes');

    element('sign-out')!.click();
    await harness.fixture.whenStable();

    expect(signOuts()).toBe(1);
    expect(TestBed.inject(Router).url).toBe('/cms/login');
  });
});
