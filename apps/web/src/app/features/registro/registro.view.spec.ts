import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideSolventaI18n } from '../../core/i18n/provide-i18n';
import { RegistroDraft } from './registro.draft';
import { RegistroView } from './registro.view';

describe('RegistroView', () => {
  let fixture: ComponentFixture<RegistroView>;
  let http: HttpTestingController;
  let navigate: jasmine.Spy;

  const host = () => fixture.nativeElement as HTMLElement;
  const element = (testId: string) =>
    host().querySelector<HTMLElement>(`[data-testid="${testId}"]`);

  function type(testId: string, value: string): void {
    const input = element(testId) as HTMLInputElement;
    input.value = value;
    input.dispatchEvent(new Event('input'));
  }

  function submit(): void {
    element('registro-form')!.dispatchEvent(new Event('submit', { cancelable: true }));
    fixture.detectChanges();
  }

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RegistroView],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        ...provideSolventaI18n(),
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(RegistroView);
    http = TestBed.inject(HttpTestingController);
    navigate = spyOn(TestBed.inject(Router), 'navigateByUrl').and.resolveTo(true);
    fixture.detectChanges();
  });

  afterEach(() => {
    http.verify();
    TestBed.inject(RegistroDraft).clear();
  });

  it('asks for name, last names, document, email and password, never for a photo', () => {
    const inputs = Array.from(host().querySelectorAll('input'));

    expect(inputs.map((input) => input.getAttribute('data-testid'))).toEqual([
      'registro-nombre',
      'registro-apellidos',
      'registro-documento',
      'registro-correo',
      'registro-contrasena',
    ]);
    expect(inputs.some((input) => input.type === 'file')).toBeFalse();
    expect(element('registro-contrasena')?.getAttribute('type')).toBe('password');
  });

  it('keeps the data and continues to consent without calling the BFF', () => {
    type('registro-nombre', 'Camila');
    type('registro-apellidos', 'Restrepo');
    type('registro-documento', '1012345678');
    type('registro-correo', 'camila@correo.com');
    type('registro-contrasena', 'secreto123');

    submit();

    http.expectNone(() => true);
    expect(TestBed.inject(RegistroDraft).alta()).toEqual({
      nombre: 'Camila',
      apellidos: 'Restrepo',
      documento: '1012345678',
      correo: 'camila@correo.com',
      contrasena: 'secreto123',
    });
    expect(navigate).toHaveBeenCalledOnceWith('/consentimiento');
  });

  it('marks each invalid field in the same view', () => {
    type('registro-correo', 'camila@');

    submit();

    expect(element('registro-nombre')?.getAttribute('aria-invalid')).toBe('true');
    expect(element('registro-nombre')?.getAttribute('aria-describedby')).toBe(
      'registro-nombre-error',
    );
    expect(element('registro-correo-error')?.getAttribute('data-issue')).toBe('format');
    expect(element('registro-correo-error')?.textContent).toContain('Escribe un correo válido.');
    expect(element('registro-contrasena-error')?.textContent).toContain('Completa este campo.');
    expect(navigate).not.toHaveBeenCalled();
    expect(TestBed.inject(RegistroDraft).alta()).toBeNull();
  });

  it('links back to the web login for an existing account', () => {
    expect(element('registro-login')?.getAttribute('href')).toBe('/login');
  });
});
