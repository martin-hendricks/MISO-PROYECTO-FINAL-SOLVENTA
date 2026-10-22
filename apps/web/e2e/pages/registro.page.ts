import assert from 'node:assert/strict';
import { Page } from 'playwright';
import { SignUp } from '../support/data/generators';

const CAMERA_CALLS = '__solventaCameraCalls';

export class RegistroPage {
  constructor(private readonly page: Page) {}

  /** Counts every camera request the portal makes from now on. */
  async watchCamera(): Promise<void> {
    await this.page.addInitScript((key) => {
      const counter = window as unknown as Record<string, number>;
      counter[key] = 0;
      const media = navigator.mediaDevices;
      if (media?.getUserMedia) {
        const original = media.getUserMedia.bind(media);
        media.getUserMedia = (constraints) => {
          counter[key] += 1;
          return original(constraints);
        };
      }
    }, CAMERA_CALLS);
  }

  async open(): Promise<void> {
    await this.page.goto('/registro');
    await this.form().waitFor({ state: 'visible' });
  }

  async openFromLogin(): Promise<void> {
    await this.page.getByTestId('login-register').click();
    await this.form().waitFor({ state: 'visible' });
  }

  async fill(alta: SignUp): Promise<void> {
    for (const [field, value] of Object.entries(alta)) {
      await this.page.getByTestId(`registro-${field}`).fill(value);
    }
    await this.page.getByTestId('registro-submit').click();
  }

  async chooseSignIn(): Promise<void> {
    await this.page.getByTestId('registro-login').click();
  }

  async expectNoPhotoOrBiometrics(): Promise<void> {
    assert.equal(await this.page.locator('input[type="file"]').count(), 0);
    const calls = await this.page.evaluate((key) => (window as never)[key], CAMERA_CALLS);
    assert.equal(calls, 0, 'the portal should not ask for the camera');
  }

  async expectConsentStep(): Promise<void> {
    await this.page.getByTestId('consentimiento').waitFor({ state: 'visible' });
    assert.equal(new URL(this.page.url()).pathname, '/consentimiento');
  }

  private form() {
    return this.page.getByTestId('registro-form');
  }
}
