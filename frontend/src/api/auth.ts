import { peticion } from './client';

export interface Usuario {
  usuario: string;
  debeCambiarPassword: boolean;
}

export const iniciarSesion = (usuario: string, password: string): Promise<Usuario> =>
  peticion<Usuario>('/api/auth/login/', { metodo: 'POST', cuerpo: { usuario, password } });

export const cerrarSesion = (): Promise<void> =>
  peticion<void>('/api/auth/logout/', { metodo: 'POST' });

export const sesionActual = (): Promise<Usuario> => peticion<Usuario>('/api/auth/me/');

export const cambiarPassword = (actual: string, nueva: string): Promise<Usuario> =>
  peticion<Usuario>('/api/auth/password/', { metodo: 'POST', cuerpo: { actual, nueva } });
