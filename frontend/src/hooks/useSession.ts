import { useCallback, useEffect, useState } from 'react';
import { cerrarSesion, iniciarSesion, sesionActual, type Usuario } from '../api/auth';

type Estado = 'comprobando' | 'anonimo' | 'autenticado';

export function useSession() {
  const [estado, setEstado] = useState<Estado>('comprobando');
  const [usuario, setUsuario] = useState<Usuario | null>(null);

  // Al cargar se pregunta si la cookie de sesion sigue viva, para no mostrar
  // el login a alguien que ya entro.
  useEffect(() => {
    let vigente = true;
    sesionActual()
      .then((u) => {
        if (!vigente) return;
        setUsuario(u);
        setEstado('autenticado');
      })
      .catch(() => {
        if (vigente) setEstado('anonimo');
      });
    return () => {
      vigente = false;
    };
  }, []);

  const entrar = useCallback(async (nombre: string, password: string) => {
    const u = await iniciarSesion(nombre, password);
    setUsuario(u);
    setEstado('autenticado');
  }, []);

  const marcarPasswordCambiada = useCallback(() => {
    setUsuario((previo) => (previo === null ? null : { ...previo, debeCambiarPassword: false }));
  }, []);

  const salir = useCallback(async () => {
    await cerrarSesion();
    setUsuario(null);
    setEstado('anonimo');
  }, []);

  return { estado, usuario, entrar, salir, marcarPasswordCambiada };
}
