import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { Role } from '../../../core/session/session.service';
import { NoPermission } from './no-permission';

describe('NoPermission', () => {
  function render(current: Role | null, required: Role) {
    TestBed.configureTestingModule({
      imports: [NoPermission],
      providers: [provideRouter([]), ...provideSolventaI18n()],
    });
    const fixture = TestBed.createComponent(NoPermission);
    fixture.componentRef.setInput('current', current);
    fixture.componentRef.setInput('required', required);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    return (testId: string) => host.querySelector<HTMLElement>(`[data-testid="${testId}"]`);
  }

  it('names the current role and the required one', () => {
    const element = render('asesor', 'operador');

    expect(element('no-permission-detail')?.textContent?.trim()).toBe(
      'Tu rol actual es Asesor. Esta sección es exclusiva del rol Operador. Solicita el cambio de rol al administrador.',
    );
  });

  it('sends the advisor back to Clientes', () => {
    const element = render('asesor', 'operador');

    expect(element('no-permission-home')?.getAttribute('href')).toBe('/cms/clientes');
  });

  it('sends the operator back to Avisos', () => {
    const element = render('operador', 'asesor');

    expect(element('no-permission-home')?.getAttribute('href')).toBe('/cms/avisos');
  });
});
