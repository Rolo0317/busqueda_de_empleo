import { llamar } from './rpc';

/** Lo que el bot leyó en el correo sobre una postulación. */
export type Categoria = 'accion_requerida' | 'contacto_humano' | 'avance' | 'rechazo';

export interface Evento {
  id: number;
  categoria: Categoria;
  motivo: string | null;
  remitente: string;
  asunto: string;
  cargo: string | null;
  enlace: string | null;
  recibido: string;
  atendido: boolean;
  vacante: string | null;
  empresa: string | null;
  plataforma: string | null;
  url: string | null;
}

export interface Embudo {
  postuladas: number;
  conRespuesta: number;
  accionRequerida: number;
  contactos: number;
  rechazos: number;
  pendientes: number;
}

export const ETIQUETA_CATEGORIA: Record<Categoria, string> = {
  accion_requerida: 'Acción requerida',
  contacto_humano: 'Te escribieron',
  avance: 'Avance',
  rechazo: 'Rechazo',
};

export const listarEventos = (limite: number, soloPendientes: boolean): Promise<Evento[]> =>
  llamar<Evento[]>('empleo_eventos', { p_limite: limite, p_solo_pendientes: soloPendientes });

export const obtenerEmbudo = (): Promise<Embudo> => llamar<Embudo>('empleo_embudo');

export const marcarAtendido = (id: number, atendido = true): Promise<void> =>
  llamar<void>('empleo_marcar_evento_atendido', { p_id: id, p_atendido: atendido });
