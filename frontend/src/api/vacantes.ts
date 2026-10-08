import { llamar } from './rpc';

/** Puntaje desde el que una vacante "califica". Igual que MIN_MATCH_SCORE del bot. */
export const UMBRAL_CALIFICA = 45;

export interface Vacante {
  id: number;
  titulo: string;
  empresa: string;
  ciudad: string;
  salario: string;
  score: number;
  estado: string;
  plataforma: string;
  url: string;
  actualizada: string;
}

export interface Resumen {
  total: number;
  aplicadas: number;
  descartadas: number;
  pendientes: number;
  conError: number;
  calificadas: number;
  promedio: number;
  preguntas: number;
  porPlataforma: Record<string, number>;
}

export interface RespuestaVacantes {
  total: number;
  vacantes: Vacante[];
}

export interface DiaDeActividad {
  dia: string;
  encontradas: number;
  postuladas: number;
}

export type Estado = '' | 'found' | 'applied' | 'discarded' | 'no_available' | 'error';

export interface Filtros {
  busqueda: string;
  soloCalificadas: boolean;
  estado: Estado;
}

export const LIMITE_LISTADO = 30;

export const listarVacantes = (filtros: Filtros): Promise<RespuestaVacantes> =>
  llamar<RespuestaVacantes>('empleo_vacantes', {
    p_busqueda: filtros.busqueda,
    p_estado: filtros.estado,
    p_min_score: filtros.soloCalificadas ? UMBRAL_CALIFICA : 0,
    p_limite: LIMITE_LISTADO,
  });

export const obtenerResumen = (): Promise<Resumen> =>
  llamar<Resumen>('empleo_resumen', { p_umbral: UMBRAL_CALIFICA });

export const obtenerActividad = (dias: number): Promise<DiaDeActividad[]> =>
  llamar<DiaDeActividad[]>('empleo_actividad', { p_dias: dias });
