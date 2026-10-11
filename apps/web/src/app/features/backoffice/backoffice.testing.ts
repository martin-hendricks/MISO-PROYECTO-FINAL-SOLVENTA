import { signal } from '@angular/core';
import { Role, SessionService } from '../../core/session/session.service';

/** Session double for back-office specs. */
export function sessionAs(role: Role) {
  let signOuts = 0;
  return {
    signOuts: () => signOuts,
    provider: {
      provide: SessionService,
      useValue: {
        role: signal<Role | null>(role),
        subject: signal<string | null>('camila.restrepo@solventa.co'),
        signOut: () => {
          signOuts += 1;
        },
      },
    },
  };
}
