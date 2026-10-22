import { TestBed } from '@angular/core/testing';
import { provideSolventaI18n } from '../../core/i18n/provide-i18n';
import { ConsentimientoView } from './consentimiento.view';

describe('ConsentimientoView', () => {
  it('names the consent step Registro continues to', () => {
    TestBed.configureTestingModule({
      imports: [ConsentimientoView],
      providers: [...provideSolventaI18n()],
    });
    const fixture = TestBed.createComponent(ConsentimientoView);
    fixture.detectChanges();

    const section = (fixture.nativeElement as HTMLElement).querySelector(
      '[data-testid="consentimiento"]',
    );
    expect(section?.textContent).toContain('Consentimiento de datos');
  });
});
