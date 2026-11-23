import assert from 'node:assert/strict';
import { Page } from 'playwright';

export class NotificacionesPage {
  constructor(private readonly page: Page) {}

  async expectForm(): Promise<void> {
    await this.page.getByTestId('notificaciones-form').waitFor({ state: 'visible' });
    assert.equal(
      (await this.page.getByTestId('notificaciones-restante-titulo').innerText()).trim(),
      '80',
    );
  }

  async write(titulo: string, cuerpo: string): Promise<void> {
    await this.page.getByTestId('notificaciones-titulo').fill(titulo);
    await this.page.getByTestId('notificaciones-cuerpo').fill(cuerpo);
  }

  async expectPreview(titulo: string, cuerpo: string): Promise<void> {
    assert.equal(
      (await this.page.getByTestId('notificaciones-preview-titulo').innerText()).trim(),
      titulo,
    );
    assert.equal(
      (await this.page.getByTestId('notificaciones-preview-cuerpo').innerText()).trim(),
      cuerpo,
    );
  }

  async send(): Promise<void> {
    await this.page.getByTestId('notificaciones-enviar').click();
  }

  async expectResult(enviadas: string): Promise<void> {
    await this.page.getByTestId('notificaciones-resultado').waitFor({ state: 'visible' });
    assert.equal((await this.page.getByTestId('notificaciones-enviadas').innerText()).trim(), enviadas);
  }

  async expectHistory(difusionId: string, titulo: string): Promise<void> {
    const item = this.page.getByTestId(`notificaciones-item-${difusionId}`);
    await item.waitFor({ state: 'visible' });
    assert.equal((await item.innerText()).trim(), titulo);
  }
}
