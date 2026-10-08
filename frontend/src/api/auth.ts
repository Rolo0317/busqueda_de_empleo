import type { Session } from '@supabase/supabase-js';
import { supabase } from '../lib/supabase';
import { llamar } from './rpc';

export async function iniciarSesion(email: string, password: string): Promise<void> {
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) throw new Error('Correo o contraseña incorrectos.');
}

export async function cerrarSesion(): Promise<void> {
  await supabase.auth.signOut();
}

export async function sesionActual(): Promise<Session | null> {
  const { data } = await supabase.auth.getSession();
  return data.session;
}

/** Tener cuenta no basta: solo los operadores ven y disparan el bot. */
export const esOperador = (): Promise<boolean> => llamar<boolean>('empleo_es_operador');

export function alCambiarSesion(manejar: (sesion: Session | null) => void): () => void {
  const { data } = supabase.auth.onAuthStateChange((_evento, sesion) => manejar(sesion));
  return () => data.subscription.unsubscribe();
}
