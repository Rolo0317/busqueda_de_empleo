import { peticion } from './client';

export interface Vacante {
  id: number;
  titulo: string;
  empresa: string;
  ciudad: string;
  salario: string;
  modalidad: string;
  score: number;
  estado: string;
  plataforma: string;
  url: string;
}

export interface ResumenVacantes {
  total: number;
  aplicadas: number;
  calificadas: number;
  promedio: number;
}

export interface RespuestaVacantes {
  total: number;
  mostradas: number;
  resumen: ResumenVacantes;
  vacantes: Vacante[];
}

export type Estado = '' | 'found' | 'applied' | 'discarded' | 'no_available';

export interface Filtros {
  busqueda: string;
  soloCalificadas: boolean;
  estado: Estado;
}

export function listarVacantes(filtros: Filtros): Promise<RespuestaVacantes> {
  const parametros = new URLSearchParams({ limite: '30' });
  if (filtros.busqueda) parametros.set('q', filtros.busqueda);
  if (filtros.soloCalificadas) parametros.set('soloCalificadas', '1');
  if (filtros.estado) parametros.set('estado', filtros.estado);
  return peticion<RespuestaVacantes>(`/api/vacantes/?${parametros}`);
}
