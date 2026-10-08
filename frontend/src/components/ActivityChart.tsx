import { useState } from 'react';
import type { DiaDeActividad } from '../api/vacantes';
import { formatearDia, formatearNumero } from '../lib/formato';

/** Dos series, colores validados para daltonismo y contraste sobre blanco. */
const SERIES = [
  { clave: 'encontradas', etiqueta: 'Encontradas', color: '#2F74A8' },
  { clave: 'postuladas', etiqueta: 'Postuladas', color: '#B8860B' },
] as const;

const ALTO = 180;
const MARGEN = { arriba: 12, derecha: 8, abajo: 26, izquierda: 34 };
const ANCHO_MAXIMO_BARRA = 12;
const SEPARACION_BARRAS = 2;
const RADIO_PUNTA = 3;
const MARCAS_EJE_Y = 4;
const CADA_CUANTOS_DIAS_ETIQUETA = 7;

/** Columna con la punta redondeada y la base recta, apoyada en el eje. */
function rutaColumna(x: number, y: number, ancho: number, alto: number): string {
  if (alto <= 0) return '';
  const r = Math.min(RADIO_PUNTA, ancho / 2, alto);
  const base = y + alto;
  return `M${x},${base}V${y + r}Q${x},${y} ${x + r},${y}H${x + ancho - r}Q${x + ancho},${y} ${x + ancho},${y + r}V${base}Z`;
}

function techoRedondo(maximo: number): number {
  if (maximo <= 0) return MARCAS_EJE_Y;
  const paso = Math.pow(10, Math.floor(Math.log10(maximo)));
  const techo = Math.ceil(maximo / paso) * paso;
  return Math.ceil(techo / MARCAS_EJE_Y) * MARCAS_EJE_Y;
}

interface Props {
  dias: DiaDeActividad[];
  anchoTotal: number;
}

export function ActivityChart({ dias, anchoTotal }: Props) {
  const [activo, setActivo] = useState<number | null>(null);

  const anchoPlot = Math.max(anchoTotal - MARGEN.izquierda - MARGEN.derecha, 100);
  const altoPlot = ALTO - MARGEN.arriba - MARGEN.abajo;
  const banda = anchoPlot / Math.max(dias.length, 1);
  const anchoBarra = Math.min(ANCHO_MAXIMO_BARRA, Math.max((banda - 6) / 2 - SEPARACION_BARRAS / 2, 2));
  const techo = techoRedondo(Math.max(0, ...dias.flatMap((d) => [d.encontradas, d.postuladas])));
  const y = (v: number) => MARGEN.arriba + altoPlot - (v / techo) * altoPlot;
  const marcas = Array.from({ length: MARCAS_EJE_Y + 1 }, (_, i) => (techo / MARCAS_EJE_Y) * i);
  const diaActivo = activo === null ? null : dias[activo];

  return (
    <figure className="grafica">
      <figcaption className="leyenda">
        {SERIES.map((s) => (
          <span key={s.clave}>
            <span className="muestra" style={{ background: s.color }} aria-hidden="true" />
            {s.etiqueta}
          </span>
        ))}
      </figcaption>

      <div className="lienzo">
        <svg
          width={anchoTotal}
          height={ALTO}
          role="img"
          aria-label={`Vacantes encontradas y postulaciones por día, últimos ${dias.length} días`}
          onMouseLeave={() => setActivo(null)}
        >
          {marcas.map((m) => (
            <g key={m}>
              <line x1={MARGEN.izquierda} x2={anchoTotal - MARGEN.derecha} y1={y(m)} y2={y(m)} className="rejilla" />
              <text x={MARGEN.izquierda - 6} y={y(m)} className="eje" textAnchor="end" dominantBaseline="middle">
                {formatearNumero(m)}
              </text>
            </g>
          ))}

          {dias.map((d, i) => {
            const centro = MARGEN.izquierda + banda * i + banda / 2;
            const xEncontradas = centro - SEPARACION_BARRAS / 2 - anchoBarra;
            const xPostuladas = centro + SEPARACION_BARRAS / 2;
            return (
              <g key={d.dia} opacity={activo === null || activo === i ? 1 : 0.45}>
                <path d={rutaColumna(xEncontradas, y(d.encontradas), anchoBarra, y(0) - y(d.encontradas))} fill={SERIES[0].color} />
                <path d={rutaColumna(xPostuladas, y(d.postuladas), anchoBarra, y(0) - y(d.postuladas))} fill={SERIES[1].color} />
                {i % CADA_CUANTOS_DIAS_ETIQUETA === (dias.length - 1) % CADA_CUANTOS_DIAS_ETIQUETA && (
                  <text x={centro} y={ALTO - 8} className="eje" textAnchor="middle">{formatearDia(d.dia)}</text>
                )}
                {/* El area sensible es toda la banda del dia, no solo la barra. */}
                <rect
                  x={MARGEN.izquierda + banda * i}
                  y={MARGEN.arriba}
                  width={banda}
                  height={altoPlot}
                  fill="transparent"
                  onMouseEnter={() => setActivo(i)}
                  onClick={() => setActivo(i)}
                />
              </g>
            );
          })}
          <line x1={MARGEN.izquierda} x2={anchoTotal - MARGEN.derecha} y1={y(0)} y2={y(0)} className="base" />
        </svg>

        {diaActivo && activo !== null && (
          <div
            className="tooltip"
            role="status"
            style={{
              left: Math.min(Math.max(MARGEN.izquierda + banda * activo + banda / 2, 70), anchoTotal - 70),
            }}
          >
            <strong>{formatearDia(diaActivo.dia)}</strong>
            {SERIES.map((s) => (
              <span key={s.clave}>
                <span className="muestra" style={{ background: s.color }} aria-hidden="true" />
                {s.etiqueta}: {formatearNumero(diaActivo[s.clave])}
              </span>
            ))}
          </div>
        )}
      </div>

      <details className="tabla-datos">
        <summary>Ver como tabla</summary>
        <table>
          <thead>
            <tr><th scope="col">Día</th>{SERIES.map((s) => <th key={s.clave} scope="col">{s.etiqueta}</th>)}</tr>
          </thead>
          <tbody>
            {[...dias].reverse().map((d) => (
              <tr key={d.dia}>
                <th scope="row">{formatearDia(d.dia)}</th>
                <td>{formatearNumero(d.encontradas)}</td>
                <td>{formatearNumero(d.postuladas)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}
