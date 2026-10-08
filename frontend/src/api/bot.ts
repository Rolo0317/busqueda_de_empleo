import { llamar } from './rpc';

export interface EstadoAgente {
  enLinea: boolean;
  maquina?: string;
  ultimoLatido?: string;
  navegadorListo?: boolean;
}

export type EstadoCorrida = 'pending' | 'running' | 'finished' | 'failed' | 'cancelled' | 'expired';

export interface ResumenCorrida {
  revisadas: number;
  aplicadas: number;
  errores: number;
  omitidas: number;
}

export interface Corrida {
  id: number;
  maxOfertas: number;
  estado: EstadoCorrida;
  maquina: string | null;
  solicitada: string;
  iniciada: string | null;
  terminada: string | null;
  codigoSalida: number | null;
  log: string | null;
  resumen: ResumenCorrida | null;
}

export const estadoAgente = (): Promise<EstadoAgente> => llamar<EstadoAgente>('empleo_estado_agente');

export const listarCorridas = (limite = 6): Promise<Corrida[]> =>
  llamar<Corrida[]>('empleo_corridas', { p_limite: limite });

export const solicitarCorrida = (maxOfertas: number): Promise<{ id: number }> =>
  llamar<{ id: number }>('empleo_solicitar_corrida', { p_max_ofertas: maxOfertas });

export const cancelarCorrida = (id: number): Promise<void> =>
  llamar<void>('empleo_cancelar_corrida', { p_id: id });

export const corridaViva = (c: Corrida | undefined): boolean =>
  c?.estado === 'pending' || c?.estado === 'running';
