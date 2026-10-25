import { of, Subject, throwError } from 'rxjs';
import { EmisionAsesor, SolicitudEmision } from './asesor-emision.gateway';
import { APROBADA, EMITIDA, RECHAZADA } from './asesor-emision.testing';
import { AsesorEmisionViewModel } from './asesor-emision.viewmodel';

describe('AsesorEmisionViewModel', () => {
  const never = () => new Subject<EmisionAsesor>();

  it('stays loading until the core decides', () => {
    const viewModel = new AsesorEmisionViewModel(() => new Subject<SolicitudEmision>(), never);

    viewModel.load();

    expect(viewModel.status()).toBe('loading');
    expect(viewModel.solicitud()).toBeNull();
    expect(viewModel.pasos()).toEqual([]);
  });

  it('waits for the advisor to issue once the core approves', () => {
    const viewModel = new AsesorEmisionViewModel(() => of(APROBADA), never);

    viewModel.load();

    expect(viewModel.status()).toBe('approved');
    expect(viewModel.pasos()).toEqual(APROBADA.pasos);
  });

  it('never issues when the core rejects', () => {
    let issued = 0;
    const viewModel = new AsesorEmisionViewModel(
      () => of(RECHAZADA),
      () => {
        issued += 1;
        return of(EMITIDA);
      },
    );

    viewModel.load();
    viewModel.issue();

    expect(viewModel.status()).toBe('rejected');
    expect(viewModel.poliza()).toBeNull();
    expect(issued).toBe(0);
  });

  it('signs and issues the approved request, then takes the core steps', () => {
    const issuing = new Subject<EmisionAsesor>();
    const ids: string[] = [];
    const viewModel = new AsesorEmisionViewModel(
      () => of(APROBADA),
      (solicitudId) => {
        ids.push(solicitudId);
        return issuing;
      },
    );
    viewModel.load();

    viewModel.issue();
    expect(viewModel.status()).toBe('issuing');

    issuing.next(EMITIDA);
    expect(viewModel.status()).toBe('issued');
    expect(ids).toEqual(['SOL-0091']);
    expect(viewModel.poliza()?.numero).toBe('POL-2026-00090102');
    expect(viewModel.pasos()).toEqual(EMITIDA.pasos);
  });

  it('retries the decision after a failure', () => {
    let attempts = 0;
    const viewModel = new AsesorEmisionViewModel(
      () => (++attempts === 1 ? throwError(() => new Error('sin red')) : of(APROBADA)),
      never,
    );

    viewModel.load();
    expect(viewModel.status()).toBe('error');

    viewModel.retry();
    expect(viewModel.status()).toBe('approved');
  });

  it('retries the issuance after it fails, keeping the decision', () => {
    let attempts = 0;
    const viewModel = new AsesorEmisionViewModel(
      () => of(APROBADA),
      () => (++attempts === 1 ? throwError(() => new Error('firma')) : of(EMITIDA)),
    );
    viewModel.load();

    viewModel.issue();
    expect(viewModel.status()).toBe('error');
    expect(viewModel.solicitud()).toEqual(APROBADA);

    viewModel.retry();
    expect(viewModel.status()).toBe('issued');
  });
});
