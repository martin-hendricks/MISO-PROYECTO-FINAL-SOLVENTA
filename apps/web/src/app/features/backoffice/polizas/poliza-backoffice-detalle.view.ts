import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { DatePipe, MoneyPipe } from '../../../core/i18n/format';
import { SessionService } from '../../../core/session/session.service';
import { ConfirmDialog } from '../confirm-dialog/confirm-dialog';
import { NoPermission } from '../no-permission/no-permission';
import { requiredRole } from '../sections';
import { Cobertura, PolizasBackofficeGateway } from './polizas-backoffice.gateway';
import { PolizaBackofficeDetalleViewModel } from './poliza-backoffice-detalle.viewmodel';

/** Fila editable del formulario de coberturas: los inputs numéricos del
 * template trabajan en string (valor crudo del <input>); convertir a number
 * solo al armar el payload evita parseos a mitad de edición (ej. "12." o
 * vacío mientras el usuario escribe). */
interface CoberturaEditable {
  nombre: string;
  sumaAsegurada: string;
  deducible: string;
}

function aEditable(c: Cobertura): CoberturaEditable {
  return { nombre: c.nombre, sumaAsegurada: String(c.sumaAsegurada), deducible: String(c.deducible) };
}

@Component({
  selector: 'sv-poliza-backoffice-detalle',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TranslatePipe, MoneyPipe, DatePipe, NoPermission, ConfirmDialog],
  templateUrl: './poliza-backoffice-detalle.view.html',
  styleUrls: ['../backoffice.page.css', './poliza-backoffice-detalle.view.css'],
})
export class PolizaBackofficeDetalleView {
  private readonly gateway = inject(PolizasBackofficeGateway);
  private readonly router = inject(Router);
  protected readonly numero = inject(ActivatedRoute).snapshot.paramMap.get('numero');
  protected readonly required = requiredRole('polizas');
  protected readonly role = inject(SessionService).role;
  protected readonly allowed = this.role() === this.required;

  protected readonly busqueda = signal('');
  protected readonly dialogoCancelarAbierto = signal(false);
  protected readonly editandoCoberturas = signal(false);
  protected readonly coberturasEditables = signal<CoberturaEditable[]>([]);

  protected readonly vm = new PolizaBackofficeDetalleViewModel(
    () => this.gateway.buscarPorNumero(this.numero!),
    () => this.gateway.renovar(this.numero!),
    (motivo) => this.gateway.cancelar(this.numero!, motivo),
    (coberturas) => this.gateway.modificarCoberturas(this.numero!, coberturas),
  );

  constructor() {
    if (this.allowed && this.numero) {
      this.vm.load();
    }
  }

  protected buscar(): void {
    const numero = this.busqueda().trim();
    if (numero) {
      void this.router.navigate(['/cms/polizas', numero]);
    }
  }

  protected abrirCancelar(): void {
    this.dialogoCancelarAbierto.set(true);
  }

  protected confirmarCancelar(motivo: string): void {
    this.dialogoCancelarAbierto.set(false);
    this.vm.cancelar(motivo);
  }

  protected abrirEditarCoberturas(): void {
    // El botón que llama esto solo existe dentro del bloque @default del
    // @switch, que ya exige vm.poliza() no nulo -- nunca se puede llamar
    // con la póliza todavía sin cargar.
    this.coberturasEditables.set(this.vm.poliza()!.coberturas.map(aEditable));
    this.editandoCoberturas.set(true);
  }

  protected cancelarEditarCoberturas(): void {
    this.editandoCoberturas.set(false);
  }

  protected actualizarFila(indice: number, campo: keyof CoberturaEditable, valor: string): void {
    this.coberturasEditables.update((filas) =>
      filas.map((fila, i) => (i === indice ? { ...fila, [campo]: valor } : fila)),
    );
  }

  protected agregarFila(): void {
    this.coberturasEditables.update((filas) => [...filas, { nombre: '', sumaAsegurada: '0', deducible: '0' }]);
  }

  protected quitarFila(indice: number): void {
    this.coberturasEditables.update((filas) => filas.filter((_, i) => i !== indice));
  }

  protected readonly puedeGuardarCoberturas = (): boolean =>
    this.coberturasEditables().length > 0 &&
    this.coberturasEditables().every((fila) => fila.nombre.trim().length > 0);

  protected guardarCoberturas(): void {
    if (!this.puedeGuardarCoberturas()) {
      return;
    }
    const coberturas: Cobertura[] = this.coberturasEditables().map((fila) => ({
      nombre: fila.nombre.trim(),
      sumaAsegurada: Number(fila.sumaAsegurada) || 0,
      deducible: Number(fila.deducible) || 0,
    }));
    this.editandoCoberturas.set(false);
    this.vm.modificarCoberturas(coberturas);
  }
}
