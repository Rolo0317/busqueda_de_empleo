import { supabase } from '../lib/supabase';

/** Toda la API del panel son funciones public.empleo_* en Postgres. */
export async function llamar<T>(funcion: string, parametros: Record<string, unknown> = {}): Promise<T> {
  const { data, error } = await supabase.rpc(funcion, parametros);
  if (error) throw new Error(error.message);
  return data as T;
}
