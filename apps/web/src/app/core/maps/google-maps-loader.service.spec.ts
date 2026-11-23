import { TestBed } from '@angular/core/testing';
import { GOOGLE_MAPS_API_KEY } from './google-maps-key';
import { GoogleMapsLoaderService } from './google-maps-loader.service';

describe('GoogleMapsLoaderService', () => {
  afterEach(() => {
    delete (window as { gm_authFailure?: () => void }).gm_authFailure;
  });

  function setup(key: string) {
    TestBed.configureTestingModule({
      providers: [{ provide: GOOGLE_MAPS_API_KEY, useValue: key }],
    });
    return TestBed.inject(GoogleMapsLoaderService);
  }

  it('resolves an empty key to no-disponible without loading a script', async () => {
    const create = spyOn(document, 'createElement').and.callThrough();
    const loader = setup('   ');

    await expectAsync(loader.cargar()).toBeResolvedTo('no-disponible');
    expect(loader.estado()).toBe('no-disponible');
    expect(create).not.toHaveBeenCalled();
  });

  it('resolves a script error to no-disponible', async () => {
    const script = fakeScript();
    const loader = setup('test-key');
    const pending = loader.cargar();

    expect(script.src).toContain('key=test-key');
    script.onerror?.(new Event('error'));
    await expectAsync(pending).toBeResolvedTo('no-disponible');
    expect(loader.estado()).toBe('no-disponible');
  });

  it('resolves gm_authFailure to no-disponible', async () => {
    fakeScript();
    const loader = setup('test-key');
    const pending = loader.cargar();

    (window as { gm_authFailure?: () => void }).gm_authFailure?.();
    await expectAsync(pending).toBeResolvedTo('no-disponible');
    expect(loader.estado()).toBe('no-disponible');
  });

  it('resolves a loaded script to disponible and reuses the same load', async () => {
    const script = fakeScript();
    const loader = setup('test-key');
    const pending = loader.cargar();

    script.onload?.(new Event('load'));
    await expectAsync(pending).toBeResolvedTo('disponible');
    expect(loader.estado()).toBe('disponible');
    await expectAsync(loader.cargar()).toBeResolvedTo('disponible');
  });
});

function fakeScript(): HTMLScriptElement {
  const script = document.createElement('script');
  spyOn(document, 'createElement').and.returnValue(script);
  spyOn(document.head, 'appendChild').and.returnValue(script);
  return script;
}
