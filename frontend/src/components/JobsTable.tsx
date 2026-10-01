import { useCallback, useEffect, useState } from 'react';
import { listarVacantes, type Estado, type RespuestaVacantes } from '../api/vacantes';

const UMBRAL = 45;
const ESPERA_ESCRITURA_MS = 300;

const ESTADOS: ReadonlyArray<{ valor: Estado; etiqueta: string }> = [
  { valor: '', etiqueta: 'Todas' },
  { valor: 'found', etiqueta: 'Sin postular' },
  { valor: 'applied', etiqueta: 'Postuladas' },
  { valor: 'discarded', etiqueta: 'Descartadas' },
];

function Esqueleto() {
  return (
    <ul className="vacantes" aria-hidden="true">
      {[0, 1, 2, 3, 4].map((i) => (
        <li key={i} className="cargando">
          <span className="puntaje hueco" />
          <div className="detalle">
            <span className="barra barra-ancha" />
            <span className="barra barra-media" />
          </div>
        </li>
      ))}
    </ul>
  );
}

export function JobsTable() {
  const [datos, setDatos] = useState<RespuestaVacantes | null>(null);
  const [busqueda, setBusqueda] = useState('');
  const [soloCalificadas, setSoloCalificadas] = useState(true);
  const [estado, setEstado] = useState<Estado>('');
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      setDatos(await listarVacantes({ busqueda, soloCalificadas, estado }));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudieron cargar las vacantes');
    } finally {
      setCargando(false);
    }
  }, [busqueda, soloCalificadas, estado]);

  // Se espera a que el usuario deje de escribir antes de consultar.
  useEffect(() => {
    const id = setTimeout(() => void cargar(), ESPERA_ESCRITURA_MS);
    return () => clearTimeout(id);
  }, [cargar]);

  const resumen = datos?.resumen;
  const hayFiltro = busqueda !== '' || estado !== '' || soloCalificadas;

  return (
    <section className="tarjeta" aria-labelledby="titulo-vacantes">
      <h2 id="titulo-vacantes">Vacantes</h2>

      {resumen && (
        <dl className="estado">
          <div><dt>Total</dt><dd>{resumen.total}</dd></div>
          <div><dt>Califican</dt><dd className="vivo">{resumen.calificadas}</dd></div>
          <div><dt>Postuladas</dt><dd>{resumen.aplicadas}</dd></div>
          <div><dt>Score prom.</dt><dd>{resumen.promedio}</dd></div>
        </dl>
      )}

      <div className="filtros">
        <input
          type="search"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          placeholder="Buscar cargo, empresa o ciudad"
          aria-label="Buscar vacantes"
        />
        <label className="casilla">
          <input
            type="checkbox"
            checked={soloCalificadas}
            onChange={(e) => setSoloCalificadas(e.target.checked)}
          />
          Solo score ≥ {UMBRAL}
        </label>
      </div>

      <div className="chips" role="group" aria-label="Filtrar por estado">
        {ESTADOS.map((e) => (
          <button
            key={e.valor}
            type="button"
            className={estado === e.valor ? 'chip activo' : 'chip'}
            aria-pressed={estado === e.valor}
            onClick={() => setEstado(e.valor)}
          >
            {e.etiqueta}
          </button>
        ))}
      </div>

      {error !== null && <p className="error" role="alert">{error}</p>}

      {cargando && datos === null && <Esqueleto />}

      {datos && (
        <>
          <p className="apoyo" aria-live="polite">
            {datos.total === 0
              ? 'Ninguna vacante coincide.'
              : `Mostrando ${datos.mostradas} de ${datos.total}, las de mayor puntaje.`}
          </p>

          {datos.total === 0 ? (
            <div className="vacio">
              <p>No hay vacantes con estos filtros.</p>
              {hayFiltro && (
                <button
                  type="button"
                  className="secundario"
                  onClick={() => { setBusqueda(''); setEstado(''); setSoloCalificadas(false); }}
                >
                  Quitar filtros
                </button>
              )}
            </div>
          ) : (
            <ul className="vacantes">
              {datos.vacantes.map((v) => (
                <li key={v.id}>
                  <span
                    className={v.score >= UMBRAL ? 'puntaje alto' : 'puntaje'}
                    title={`Compatibilidad ${v.score} sobre 100`}
                  >
                    {v.score}
                  </span>
                  <div className="detalle">
                    <a href={v.url} target="_blank" rel="noreferrer">{v.titulo}</a>
                    <p>{v.empresa} · {v.ciudad || 'sin ciudad'}</p>
                    <p className="meta">
                      <span className="salario">{v.salario}</span>
                      <span className="fuente">{v.plataforma}</span>
                      {v.estado === 'applied' && <span className="sello">postulada</span>}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  );
}
