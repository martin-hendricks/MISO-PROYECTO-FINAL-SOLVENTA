import { TestBed } from '@angular/core/testing';
import { provideSolventaI18n } from '../../../core/i18n/provide-i18n';
import { ConfirmDialog } from './confirm-dialog';

describe('ConfirmDialog', () => {
  function render(requiereMotivo: boolean) {
    TestBed.configureTestingModule({
      imports: [ConfirmDialog],
      providers: [...provideSolventaI18n()],
    });
    const fixture = TestBed.createComponent(ConfirmDialog);
    fixture.componentRef.setInput('titulo', 'Cancelar póliza');
    fixture.componentRef.setInput('advertencia', 'Esta acción es irreversible.');
    fixture.componentRef.setInput('requiereMotivo', requiereMotivo);
    fixture.detectChanges();
    const host = fixture.nativeElement as HTMLElement;
    return { fixture, host };
  }

  function byTestId(host: HTMLElement, testId: string) {
    return host.querySelector<HTMLElement>(`[data-testid="${testId}"]`);
  }

  it('without requiereMotivo, confirm is enabled from the start and emits an empty reason', () => {
    const { fixture, host } = render(false);
    let emitido: string | undefined;
    fixture.componentInstance.confirmar.subscribe((motivo) => (emitido = motivo));

    expect(byTestId(host, 'confirm-dialog-motivo')).toBeNull();
    const confirmar = byTestId(host, 'confirm-dialog-confirmar') as HTMLButtonElement;
    expect(confirmar.disabled).toBeFalse();

    confirmar.click();

    expect(emitido).toBe('');
  });

  it('with requiereMotivo, confirm stays disabled until a non-blank reason is typed', () => {
    const { fixture, host } = render(true);
    const confirmar = byTestId(host, 'confirm-dialog-confirmar') as HTMLButtonElement;
    expect(confirmar.disabled).toBeTrue();

    const motivo = byTestId(host, 'confirm-dialog-motivo') as HTMLTextAreaElement;
    motivo.value = '   ';
    motivo.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    expect(confirmar.disabled).toBeTrue();

    motivo.value = '  El cliente lo pidió  ';
    motivo.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    expect(confirmar.disabled).toBeFalse();
  });

  it('emits the trimmed reason on confirm', () => {
    const { fixture, host } = render(true);
    let emitido: string | undefined;
    fixture.componentInstance.confirmar.subscribe((motivo) => (emitido = motivo));

    const motivo = byTestId(host, 'confirm-dialog-motivo') as HTMLTextAreaElement;
    motivo.value = '  El cliente lo pidió  ';
    motivo.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    (byTestId(host, 'confirm-dialog-confirmar') as HTMLButtonElement).click();

    expect(emitido).toBe('El cliente lo pidió');
  });

  it('clicking confirm while disabled does not emit', () => {
    const { fixture, host } = render(true);
    let emitido = false;
    fixture.componentInstance.confirmar.subscribe(() => (emitido = true));

    (byTestId(host, 'confirm-dialog-confirmar') as HTMLButtonElement).click();

    expect(emitido).toBeFalse();
  });

  it('calling onConfirmar directly while not allowed is a no-op (defensive guard)', () => {
    const { fixture } = render(true);
    let emitido = false;
    fixture.componentInstance.confirmar.subscribe(() => (emitido = true));

    (fixture.componentInstance as unknown as { onConfirmar(): void }).onConfirmar();

    expect(emitido).toBeFalse();
  });

  it('cancelar emits without needing a reason', () => {
    const { fixture, host } = render(true);
    let cancelado = false;
    fixture.componentInstance.cancelar.subscribe(() => (cancelado = true));

    (byTestId(host, 'confirm-dialog-cancelar') as HTMLButtonElement).click();

    expect(cancelado).toBeTrue();
  });
});
