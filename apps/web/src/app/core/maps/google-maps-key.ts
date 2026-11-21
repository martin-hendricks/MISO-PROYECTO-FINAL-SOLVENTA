import { InjectionToken } from '@angular/core';

/**
 * Google Maps JavaScript API key for the provider map only.
 *
 * The factory stays empty in the repo. deploy-web.yml replaces this line
 * with the GOOGLE_MAPS_API_KEY secret before the production build.
 * Keep the factory line byte-for-byte: the deploy step matches it literally.
 */
export const GOOGLE_MAPS_API_KEY = new InjectionToken<string>('GOOGLE_MAPS_API_KEY', {
  factory: () => '',
});
