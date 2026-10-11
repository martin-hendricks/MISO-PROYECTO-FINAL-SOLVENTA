import { Role } from '../../core/session/session.service';

export interface LoginVariant {
  /** Role the channel asks for. Left out when the BFF assigns it. */
  role?: Role;
  home: string;
  /** i18n branch with the claim, body and hint of the channel. */
  copy: string;
  canRegister: boolean;
}

export const CUSTOMER_LOGIN: LoginVariant = {
  role: 'cliente',
  home: '/user',
  copy: 'login.customer',
  canRegister: true,
};

export const BACKOFFICE_LOGIN: LoginVariant = {
  home: '/cms',
  copy: 'login.backoffice',
  canRegister: false,
};
