import { useState } from 'react';
import { estadoBotContinuo, pausarBotContinuo, type AlertaBot, type EstadoBotContinuo } from '../api/bot';
import { useSondeo } from '../hooks/useSondeo';
import { haceCuanto } from '../lib/formato';

// El supervisor late cada 30 s: mirar cada 30 s basta para ver una caida pronto.
const INTERVALO_MS = 30_000;
const PATRON_CICLO = /revisadas=(\d+) \| aplicadas=(\d+)/;

const TEXTO_ALERTA: Record<AlertaBot, (e: EstadoBotContinuo) => string> = {
  supervisor_apagado: (e) =>
    `El supervisor no reporta${e.latido ? ` desde ${haceCuanto(e.latido)}` : ''}: la PC está apagada `
    + 'o la tarea de Windows no corre. Revisa scripts\\instalar_supervisor.ps1.',
  bot_detenido: () => 'El bot no está corriendo. El supervisor lo relanzará en la próxima revisión.',
  sin_actividad: (e) =>
    `Sin actividad${e.actividad ? ` desde ${haceCuanto(e.actividad)}` : ''}: el bot puede estar colgado. `
    + 'El supervisor lo reinicia solo a los 20 minutos de silencio.',
};

/** El RESUMEN CICLO del log, en cifras legibles. */
function resumenDelCiclo(linea: string | null | undefined): string | null {
  const encontrado = linea ? PATRON_CICLO.exec(linea) : null;
  return encontrado ? `${encontrado[2]} postuladas de ${encontrado[1]} revisadas` : null;
}

export function BotContinuo() {
  const estado = useSondeo(estadoBotContinuo, INTERVALO_MS);
  const [cambiando, setCambiando] = useState(false);
  const [errorAccion, setErrorAccion] = useState<string | null>(null);
  const e = estado.datos;

  async function alternarPausa() {
    if (!e) return;
    setCambiando(true);
    try {
      await pausarBotContinuo(!e.pausado);
      setErrorAccion(null);
      await estado.refrescar();
    } catch (error) {
      setErrorAccion(error instanceof Error ? error.message : 'No se pudo cambiar la pausa');
    } finally {
      setCambiando(false);
    }
  }

  const ciclo = resumenDelCiclo(e?.ultimoCiclo);
  const error = errorAccion ?? estado.error;

  return (
    <section className="tarjeta" aria-labelledby="titulo-continuo">
      <h2 id="titulo-continuo">Bot continuo</h2>

      {error !== null && <p className="error" role="alert">{error}</p>}
      {e === null && error === null && <p className="apoyo">Consultando el supervisor…</p>}

      {e && (
        <>
          {e.alerta && <p className="error" role="alert">{TEXTO_ALERTA[e.alerta](e)}</p>}

          <p className={e.alerta || e.pausado ? 'agente apagado' : 'agente encendido'}>
            <span className="punto" aria-hidden="true" />
            {e.pausado ? 'En pausa' : e.procesoVivo ? 'Trabajando' : 'Detenido'}
            {e.maquina && <span className="apoyo"> · {e.maquina}</span>}
          </p>

          <dl className="estado">
            {e.actividad && <div><dt>Última actividad</dt><dd>{haceCuanto(e.actividad)}</dd></div>}
            {ciclo && <div><dt>Último ciclo</dt><dd>{ciclo}</dd></div>}
            {e.reinicios !== undefined && <div><dt>Reinicios automáticos</dt><dd>{e.reinicios}</dd></div>}
          </dl>

          {e.maquina && (
            <div className="acciones">
              <button type="button" className="secundario" disabled={cambiando} onClick={() => void alternarPausa()}>
                {cambiando ? 'Enviando…' : e.pausado ? 'Reanudar bot' : 'Pausar bot'}
              </button>
            </div>
          )}
          <p className="apoyo">
            {e.pausado
              ? 'En pausa el supervisor no relanza el bot. Puedes seguir usando “Ejecutar” para corridas puntuales.'
              : 'Pausar detiene el bot y evita que el supervisor lo vuelva a lanzar hasta que reanudes.'}
          </p>
        </>
      )}
    </section>
  );
}
