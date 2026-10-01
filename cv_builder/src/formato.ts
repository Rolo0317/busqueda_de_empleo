/** Utilidades de texto que comparten las dos versiones del CV. */

/** Los datos vienen del perfil propio, pero escapar evita que un guion o un & rompa el HTML. */
export function esc(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/** Quita el marcado que el perfil trae para la version de diseño (negritas, spans). */
export function sinEtiquetas(html: string): string {
  return html.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
}

const MESES = [
  'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
  'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic',
] as const;

/** "2026-06-17" -> "Jun 2026" */
export function mesAnio(iso: string): string {
  const [year, month] = iso.split('-');
  const index = Number(month) - 1;
  return MESES[index] !== undefined ? `${MESES[index]} ${year}` : (year ?? iso);
}
