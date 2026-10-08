import { useCallback, useEffect, useRef, useState } from 'react';
import {
  cancelarCorrida,
  corridaViva,
  estadoAgente,
  listarCorridas,
  solicitarCorrida,
  type Corrida,
  type EstadoAgente,
  type EstadoCorrida,
} from '../api/bot';
import { useSondeo } from '../hooks/useSondeo';
import { formatearFechaHora, haceCuanto } from '../lib/formato';

const TOPES = [5, 10, 20] as const;
const SONDEO_EN_CURSO_MS = 3000;
const SONDEO_EN_REPOSO_MS = 15000;
const LINEAS_VISIBLES_DEL_LOG = 14;

const ETIQUETA_ESTADO: Record<EstadoCorrida, string> = {
  pending: 'En cola: esperando a la PC',
  running: 'Corriendo',
  finished: 'Terminó',
  failed: 'Falló',
  cancelled: 'Cancelada',
  expired: 'Caducó sin ejecutarse',
};

interface Props {
  onCorridaTerminada: () => void;
}

function Agente({ agente }: { agente: EstadoAgente | null }) {
  if (agente === null) return <p className="apoyo">Consultando la PC…</p>;
  if (!agente.enLinea) {
    return (
      <p className="agente apagado">
        <span className="punto" aria-hidden="true" />
        PC desconectada
        {agente.ultimoLatido && <span className="apoyo"> · última señal {haceCuanto(agente.ultimoLatido)}</span>}
      </p>
    );
  }
  return (
    <p className="agente encendido">
      <span className="punto" aria-hidden="true" />
      PC lista ({agente.maquina})
      <span className="apoyo">
        {' · '}navegador {agente.navegadorListo ? 'abierto' : 'cerrado (se abrirá solo)'}
      </span>
    </p>
  );
}

function DetalleCorrida({ corrida, onCancelar }: { corrida: Corrida; onCancelar: () => void }) {
  const log = (corrida.log ?? '').split('\n').slice(-LINEAS_VISIBLES_DEL_LOG).join('\n');
  return (
    <div className="corrida">
      <dl className="estado">
        <div>
          <dt>Corrida #{corrida.id}</dt>
          <dd className={corridaViva(corrida) ? 'vivo' : ''}>{ETIQUETA_ESTADO[corrida.estado]}</dd>
        </div>
        <div>
          <dt>Tope</dt>
          <dd>{corrida.maxOfertas}</dd>
        </div>
        {corrida.resumen && (
          <>
            <div><dt>Revisadas</dt><dd>{corrida.resumen.revisadas}</dd></div>
            <div><dt>Postuladas</dt><dd className="vivo">{corrida.resumen.aplicadas}</dd></div>
            <div><dt>Errores</dt><dd>{corrida.resumen.errores}</dd></div>
          </>
        )}
      </dl>
      <p className="apoyo">
        Pedida {formatearFechaHora(corrida.solicitada)}
        {corrida.terminada && ` · terminó ${formatearFechaHora(corrida.terminada)}`}
      </p>
      {log && (
        <pre className="log" aria-label="Últimas líneas del registro del bot" tabIndex={0}>{log}</pre>
      )}
      {corrida.estado === 'pending' && (
        <button type="button" className="secundario" onClick={onCancelar}>Cancelar solicitud</button>
      )}
    </div>
  );
}

export function BotPanel({ onCorridaTerminada }: Props) {
  const [tope, setTope] = useState<number>(TOPES[1]);
  const [confirmando, setConfirmando] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cargarCorridas = useCallback(() => listarCorridas(), []);
  const corridas = useSondeo(cargarCorridas, null);
  const ultima = corridas.datos?.[0];
  const viva = corridaViva(ultima);
  const intervalo = viva ? SONDEO_EN_CURSO_MS : SONDEO_EN_REPOSO_MS;

  const agente = useSondeo(estadoAgente, intervalo);
  const { refrescar: refrescarCorridas } = corridas;

  useEffect(() => {
    const id = setInterval(() => {
      if (document.visibilityState === 'visible') void refrescarCorridas();
    }, intervalo);
    return () => clearInterval(id);
  }, [intervalo, refrescarCorridas]);

  // Cuando una corrida pasa de viva a terminada, las cifras del panel cambiaron.
  const estabaViva = useRef(false);
  useEffect(() => {
    if (estabaViva.current && !viva) onCorridaTerminada();
    estabaViva.current = viva;
  }, [viva, onCorridaTerminada]);

  async function lanzar() {
    setError(null);
    setEnviando(true);
    try {
      await solicitarCorrida(tope);
      setConfirmando(false);
      await refrescarCorridas();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo solicitar la corrida');
    } finally {
      setEnviando(false);
    }
  }

  async function cancelar(id: number) {
    try {
      await cancelarCorrida(id);
      await refrescarCorridas();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo cancelar');
    }
  }

  const pcApagada = agente.datos !== null && !agente.datos.enLinea;

  return (
    <section className="tarjeta" aria-labelledby="titulo-bot">
      <h2 id="titulo-bot">Ejecutar bot</h2>

      <Agente agente={agente.datos} />

      <p className="apoyo">
        Busca en Magneto y Computrabajo, postula hasta el tope que elijas y se detiene.
        Corre en tu PC, con tu navegador y tus sesiones; este botón solo le da la orden.
        {pcApagada && ' Prende la PC y deja corriendo iniciar_agente.ps1: la orden caduca en 30 minutos.'}
      </p>

      <div className="chips" role="radiogroup" aria-label="Tope de postulaciones">
        {TOPES.map((t) => (
          <button
            key={t}
            type="button"
            role="radio"
            aria-checked={tope === t}
            className={tope === t ? 'chip activo' : 'chip'}
            onClick={() => setTope(t)}
            disabled={viva}
          >
            Hasta {t}
          </button>
        ))}
      </div>

      {(error ?? corridas.error) !== null && <p className="error" role="alert">{error ?? corridas.error}</p>}

      {/* Confirmacion explicita: una postulacion enviada no se puede retirar. */}
      {confirmando ? (
        <div className="confirmar">
          <p>
            Vas a enviar hasta <strong>{tope} postulaciones reales</strong> a tu nombre.
            No se pueden deshacer.
          </p>
          <div className="acciones">
            <button type="button" onClick={() => void lanzar()} disabled={enviando} className="peligro">
              {enviando ? 'Enviando orden…' : `Sí, postular hasta ${tope}`}
            </button>
            <button type="button" onClick={() => setConfirmando(false)} className="secundario">
              Cancelar
            </button>
          </div>
        </div>
      ) : (
        <button type="button" onClick={() => setConfirmando(true)} disabled={viva}>
          {viva ? 'Hay una corrida en curso' : 'Ejecutar'}
        </button>
      )}

      {ultima && <DetalleCorrida corrida={ultima} onCancelar={() => void cancelar(ultima.id)} />}

      {corridas.datos && corridas.datos.length > 1 && (
        <details className="historial">
          <summary>Corridas anteriores</summary>
          <ul>
            {corridas.datos.slice(1).map((c) => (
              <li key={c.id}>
                <span>#{c.id} · {formatearFechaHora(c.solicitada)}</span>
                <span>{ETIQUETA_ESTADO[c.estado]}{c.resumen ? ` · ${c.resumen.aplicadas} postuladas` : ''}</span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
