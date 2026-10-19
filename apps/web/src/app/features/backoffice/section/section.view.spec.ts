import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { Role } from '../../../core/session/session.service';
import { sessionAs } from '../backoffice.testing';
import { Section } from '../sections';
import { SectionView } from './section.view';

describe('SectionView', () => {
  function render(section: Section, role: Role) {
    TestBed.configureTestingModule({
      imports: [SectionView],
      providers: [
        provideRouter([]),
        ...provideSolventaI18n(),
        sessionAs(role).provider,
        { provide: ActivatedRoute, useValue: { snapshot: { data: { section } } } },
      ],
    });
    const fixture = TestBed.createComponent(SectionView);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    return {
      host,
      element: (testId: string) => host.querySelector<HTMLElement>(`[data-testid="${testId}"]`),
    };
  }

  it('replaces only the content when the advisor opens Avisos', () => {
    const { host, element } = render('avisos', 'asesor');

    expect(host.querySelector('h1')?.textContent).toContain('Avisos de siniestro');
    expect(element('section-avisos')?.getAttribute('data-state')).toBe('no-permission');
    expect(element('no-permission')?.getAttribute('data-current')).toBe('asesor');
    expect(element('no-permission')?.getAttribute('data-required')).toBe('operador');
    expect(element('section-pending')).toBeNull();
  });

  it('lets the operator into Avisos', () => {
    const { host, element } = render('avisos', 'operador');

    expect(element('section-avisos')?.getAttribute('data-state')).toBe('pending');
    expect(element('no-permission')).toBeNull();
    expect(host.textContent).toContain('camila.restrepo@solventa.co · Operador');
  });

  it('keeps the advisor sections away from the operator', () => {
    const { element } = render('cotizaciones', 'operador');

    expect(element('no-permission')?.getAttribute('data-required')).toBe('asesor');
  });

  it('lets the advisor into Pólizas', () => {
    const { host, element } = render('polizas', 'asesor');

    expect(host.querySelector('h1')?.textContent).toContain('Pólizas');
    expect(element('section-pending')).not.toBeNull();
  });
});
