import { useCallback, useState } from 'react';
import {
  ETIQUETA_CATEGORIA,
  listarEventos,
  marcarAtendido,
  obtenerEmbudo,
  type Evento,
} from '../api/seguimiento';
import { useSondeo } from '../hooks/useSondeo';
import { formatearNumero, haceCuanto } from '../lib/formato';

// El bot lee el correo cada 30 min; mirar cada 2 min basta para verlo pronto.
const INTERVALO_MS = 120_000;
const LIMITE_HISTORIAL = 40;

const cargarPendientes = () => listarEventos(20, true);
const cargarHistorial = () => listarEventos(LIMITE_HISTORIAL, false);

/** Nombre del cargo tal como mejor se conozca: la vacante postulada o el asunto. */
const titulo = (e: Evento): string => e.vacante ?? e.cargo ?? e.asunto;
const origen = (e: Evento): string => e.empresa ?? e.remitente.replace(/<.*>/, '').replace(/"/g, '').trim();

interface Props {
  version: number;
}

export function Seguimiento({ version }: Props) {
  const embudo = useSondeo(obtenerEmbudo, INTERVALO_MS, version);
  const pendientes = useSondeo(cargarPendientes, INTERVALO_MS, version);
  const historial = useSondeo(cargarHistorial, INTERVALO_MS, version);
  const [marcando, setMarcando] = useState<number | null>(null);
  const [errorAccion, setErrorAccion] = useState<string | null>(null);

  const atender = useCallback(async (id: number) => {
    setMarcando(id);
    try {
      await marcarAtendido(id);
      setErrorAccion(null);
      await Promise.all([pendientes.refrescar(), embudo.refrescar(), historial.refrescar()]);
    } catch (e) {
      setErrorAccion(e instanceof Error ? e.message : 'No se pudo marcar como atendido');
    } finally {
      setMarcando(null);
    }
  }, [pendientes, embudo, historial]);

  const e = embudo.datos;
  const error = errorAccion ?? embudo.error ?? pendientes.error ?? historial.error;

  return (
    <section className="tarjeta" aria-labelledby="titulo-seguimiento">
      <h2 id="titulo-seguimiento">Seguimiento</h2>

      {error !== null && <p className="error" role="alert">{error}</p>}

      {e && (
        <dl className="estado cifras">
          <div><dt>Por atender</dt><dd className={e.pendientes > 0 ? 'vivo' : undefined}>{formatearNumero(e.pendientes)}</dd></div>
          <div><dt>Con respuesta</dt><dd>{formatearNumero(e.conRespuesta)}</dd></div>
          <div><dt>Pruebas y entrevistas</dt><dd>{formatearNumero(e.accionRequerida)}</dd></div>
          <div><dt>Te escribieron</dt><dd>{formatearNumero(e.contactos)}</dd></div>
          <div><dt>Rechazos</dt><dd>{formatearNumero(e.rechazos)}</dd></div>
        </dl>
      )}

      {pendientes.datos && (
        pendientes.datos.length === 0 ? (
          <p className="apoyo">Nada pendiente: no hay pruebas, entrevistas ni mensajes sin atender.</p>
        ) : (
          <ul className="vacantes" aria-label="Pendientes por atender">
            {pendientes.datos.map((ev) => (
              <li key={ev.id}>
                <div className="detalle">
                  {ev.enlace
                    ? <a href={ev.enlace} target="_blank" rel="noreferrer">{titulo(ev)}</a>
                    : <strong>{titulo(ev)}</strong>}
                  <p>{origen(ev)} · {haceCuanto(ev.recibido)}</p>
                  <p className="meta">
                    <span className="salario">{ev.motivo ?? ETIQUETA_CATEGORIA[ev.categoria]}</span>
                    {ev.plataforma && <span className="fuente">{ev.plataforma}</span>}
                  </p>
                </div>
                <button
                  type="button"
                  className="secundario"
                  disabled={marcando === ev.id}
                  onClick={() => void atender(ev.id)}
                >
                  {marcando === ev.id ? 'Marcando…' : 'Atendido'}
                </button>
              </li>
            ))}
          </ul>
        )
      )}

      {historial.datos && historial.datos.length > 0 && (
        <details className="historial">
          <summary>Historial del correo ({historial.datos.length})</summary>
          <ul>
            {historial.datos.map((ev) => (
              <li key={ev.id}>
                <span>
                  <strong>{ETIQUETA_CATEGORIA[ev.categoria]}</strong> · {titulo(ev)} · {origen(ev)}
                </span>
                <span>{haceCuanto(ev.recibido)}{ev.atendido ? ' · atendido' : ''}</span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
