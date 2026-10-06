import { Injectable } from '@angular/core';
import { TranslateLoader, TranslationObject } from '@ngx-translate/core';
import { Observable, of } from 'rxjs';
import esCL from './es-CL.json';
import esCO from './es-CO.json';
import esMX from './es-MX.json';
import esPE from './es-PE.json';

const catalogs: Record<string, TranslationObject> = {
  'es-CL': esCL,
  'es-CO': esCO,
  'es-MX': esMX,
  'es-PE': esPE,
};

@Injectable()
export class CatalogTranslateLoader extends TranslateLoader {
  override getTranslation(lang: string): Observable<TranslationObject> {
    return of(catalogs[lang] ?? catalogs['es-CO']);
  }
}
