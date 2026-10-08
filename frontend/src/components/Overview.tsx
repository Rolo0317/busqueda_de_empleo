import { useCallback, useEffect, useRef, useState } from 'react';
import { obtenerActividad, obtenerResumen, UMBRAL_CALIFICA } from '../api/vacantes';
import { useSondeo } from '../hooks/useSondeo';
import { formatearNumero } from '../lib/formato';
import { ActivityChart } from './ActivityChart';

const RANGOS = [14, 30, 90] as const;

/** Mide el ancho disponible para que el SVG dibuje a escala real, sin deformar texto. */
function useAncho<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [ancho, setAncho] = useState(0);
  useEffect(() => {
    const elemento = ref.current;
    if (!elemento) return;
    const observador = new ResizeObserver(([entrada]) => setAncho(Math.floor(entrada.contentRect.width)));
    observador.observe(elemento);
    return () => observador.disconnect();
  }, []);
  return { ref, ancho };
}

interface Props {
  version: number;
}

export function Overview({ version }: Props) {
  const [dias, setDias] = useState<number>(30);
  const { ref, ancho } = useAncho<HTMLDivElement>();

  // `version` cambia cuando termina una corrida: obliga a recargar las cifras.
  const cargarActividad = useCallback(() => obtenerActividad(dias), [dias]);
  const resumen = useSondeo(obtenerResumen, null, version);
  const actividad = useSondeo(cargarActividad, null, version);
  const r = resumen.datos;
  const error = resumen.error ?? actividad.error;

  return (
    <section className="tarjeta" aria-labelledby="titulo-resumen">
      <h2 id="titulo-resumen">Resumen</h2>

      {error !== null && <p className="error" role="alert">{error}</p>}

      {r && (
        <dl className="estado cifras">
          <div><dt>Postuladas</dt><dd className="destacada">{formatearNumero(r.aplicadas)}</dd></div>
          <div><dt>Vacantes vistas</dt><dd>{formatearNumero(r.total)}</dd></div>
          <div><dt>Califican (≥ {UMBRAL_CALIFICA})</dt><dd>{formatearNumero(r.calificadas)}</dd></div>
          <div><dt>Sin postular</dt><dd>{formatearNumero(r.pendientes)}</dd></div>
          <div><dt>Descartadas</dt><dd>{formatearNumero(r.descartadas)}</dd></div>
          <div><dt>Preguntas respondidas</dt><dd>{formatearNumero(r.preguntas)}</dd></div>
        </dl>
      )}

      <div className="subtitulo">
        <h3>Actividad diaria</h3>
        <div className="chips" role="radiogroup" aria-label="Rango de días">
          {RANGOS.map((n) => (
            <button
              key={n}
              type="button"
              role="radio"
              aria-checked={dias === n}
              className={dias === n ? 'chip activo' : 'chip'}
              onClick={() => setDias(n)}
            >
              {n} días
            </button>
          ))}
        </div>
      </div>

      <div ref={ref}>
        {actividad.datos && ancho > 0
          ? <ActivityChart dias={actividad.datos} anchoTotal={ancho} />
          : <div className="grafica-cargando" aria-hidden="true" />}
      </div>
    </section>
  );
}
