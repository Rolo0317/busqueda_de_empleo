import { useCallback, useEffect, useState } from 'react';
import { ejecutarBot, estadoBot, type EstadoBot } from '../api/bot';

const MAX_OFERTAS = 20;
const INTERVALO_SONDEO_MS = 5000;

export function BotPanel() {
  const [estado, setEstado] = useState<EstadoBot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirmando, setConfirmando] = useState(false);
  const [lanzando, setLanzando] = useState(false);

  const refrescar = useCallback(async () => {
    try {
      setEstado(await estadoBot());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo consultar el estado');
    }
  }, []);

  useEffect(() => {
    void refrescar();
  }, [refrescar]);

  // Solo se sondea mientras hay algo que mirar.
  useEffect(() => {
    if (estado?.corriendo !== true) return;
    const id = setInterval(() => void refrescar(), INTERVALO_SONDEO_MS);
    return () => clearInterval(id);
  }, [estado?.corriendo, refrescar]);

  async function lanzar() {
    setError(null);
    setLanzando(true);
    try {
      setEstado(await ejecutarBot(MAX_OFERTAS));
      setConfirmando(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo ejecutar');
    } finally {
      setLanzando(false);
    }
  }

  const corriendo = estado?.corriendo === true;

  return (
    <section className="tarjeta">
      <h2>Ejecutar bot</h2>

      <p className="apoyo">
        Postula hasta <strong>{MAX_OFERTAS} ofertas</strong> en una sola pasada y se detiene.
        No queda corriendo en bucle.
      </p>

      <dl className="estado">
        <div>
          <dt>Estado</dt>
          <dd className={corriendo ? 'vivo' : ''}>{corriendo ? 'Corriendo' : 'Detenido'}</dd>
        </div>
        {estado?.iniciado != null && (
          <div>
            <dt>Último inicio</dt>
            <dd>{new Date(estado.iniciado).toLocaleString('es-CO')}</dd>
          </div>
        )}
        {estado?.codigoSalida != null && (
          <div>
            <dt>Salida</dt>
            <dd>{estado.codigoSalida === 0 ? 'Terminó bien' : `Código ${estado.codigoSalida}`}</dd>
          </div>
        )}
      </dl>

      {error !== null && <p className="error" role="alert">{error}</p>}

      {/* Confirmacion explicita: una postulacion enviada no se puede retirar. */}
      {confirmando ? (
        <div className="confirmar">
          <p>
            Vas a enviar postulaciones reales a tu nombre. <strong>No se pueden deshacer.</strong>
          </p>
          <div className="acciones">
            <button onClick={() => void lanzar()} disabled={lanzando} className="peligro">
              {lanzando ? 'Lanzando…' : `Sí, postular a ${MAX_OFERTAS}`}
            </button>
            <button onClick={() => setConfirmando(false)} className="secundario">
              Cancelar
            </button>
          </div>
        </div>
      ) : (
        <button onClick={() => setConfirmando(true)} disabled={corriendo}>
          {corriendo ? 'Ya está corriendo' : 'Ejecutar'}
        </button>
      )}
    </section>
  );
}
