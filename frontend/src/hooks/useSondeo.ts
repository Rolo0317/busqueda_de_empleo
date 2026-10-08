import { useCallback, useEffect, useRef, useState } from 'react';

interface Sondeo<T> {
  datos: T | null;
  error: string | null;
  refrescar: () => Promise<void>;
}

/**
 * Carga un dato y lo vuelve a pedir cada `intervaloMs` mientras la pestana
 * este visible. Con intervalo null solo carga cuando cambian `cargar` o `clave`
 * (una clave nueva es la forma de pedir "recarga ya").
 */
export function useSondeo<T>(cargar: () => Promise<T>, intervaloMs: number | null, clave = 0): Sondeo<T> {
  const [datos, setDatos] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const vigente = useRef(true);

  const refrescar = useCallback(async () => {
    try {
      const nuevos = await cargar();
      if (!vigente.current) return;
      setDatos(nuevos);
      setError(null);
    } catch (e) {
      if (vigente.current) setError(e instanceof Error ? e.message : 'No se pudo cargar');
    }
  }, [cargar]);

  useEffect(() => {
    vigente.current = true;
    void refrescar();
    return () => {
      vigente.current = false;
    };
  }, [refrescar, clave]);

  useEffect(() => {
    if (intervaloMs === null) return;
    const id = setInterval(() => {
      if (document.visibilityState === 'visible') void refrescar();
    }, intervaloMs);
    return () => clearInterval(id);
  }, [intervaloMs, refrescar]);

  return { datos, error, refrescar };
}
