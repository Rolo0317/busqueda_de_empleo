import { useCallback, useEffect, useState } from 'react';
import type { Session } from '@supabase/supabase-js';
import { alCambiarSesion, cerrarSesion, esOperador, iniciarSesion, sesionActual } from '../api/auth';

type Estado = 'comprobando' | 'anonimo' | 'sin-permiso' | 'autenticado';

async function estadoDe(sesion: Session | null): Promise<Estado> {
  if (sesion === null) return 'anonimo';
  try {
    return (await esOperador()) ? 'autenticado' : 'sin-permiso';
  } catch {
    return 'sin-permiso';
  }
}

export function useSession() {
  const [estado, setEstado] = useState<Estado>('comprobando');
  const [correo, setCorreo] = useState<string | null>(null);

  const aplicar = useCallback(async (sesion: Session | null) => {
    setCorreo(sesion?.user.email ?? null);
    setEstado(await estadoDe(sesion));
  }, []);

  // Supabase guarda la sesion en el navegador: quien ya entro no ve el login.
  useEffect(() => {
    void sesionActual().then(aplicar);
    return alCambiarSesion((sesion) => {
      // El callback de Supabase no debe esperar otras llamadas a Supabase.
      setTimeout(() => void aplicar(sesion), 0);
    });
  }, [aplicar]);

  const entrar = useCallback(async (email: string, password: string) => {
    await iniciarSesion(email, password);
  }, []);

  const salir = useCallback(async () => {
    await cerrarSesion();
  }, []);

  return { estado, correo, entrar, salir };
}
