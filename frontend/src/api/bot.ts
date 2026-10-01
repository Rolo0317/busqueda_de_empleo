import { peticion } from './client';

export interface EstadoBot {
  corriendo: boolean;
  iniciado: string | null;
  terminado: string | null;
  codigoSalida: number | null;
  maxOfertas: number | null;
  log: string | null;
}

export const estadoBot = (): Promise<EstadoBot> => peticion<EstadoBot>('/api/bot/status/');

export const ejecutarBot = (maxOfertas: number): Promise<EstadoBot> =>
  peticion<EstadoBot>('/api/bot/run/', { metodo: 'POST', cuerpo: { maxOfertas } });
