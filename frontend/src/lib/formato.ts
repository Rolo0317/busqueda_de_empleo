const fechaHora = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' });
const diaCorto = new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'short', timeZone: 'UTC' });
const numero = new Intl.NumberFormat('es-CO');

export const formatearFechaHora = (iso: string): string => fechaHora.format(new Date(iso));

/** Los dias llegan como 'YYYY-MM-DD'; se leen en UTC para no correrlos un dia. */
export const formatearDia = (dia: string): string => diaCorto.format(new Date(`${dia}T00:00:00Z`));

export const formatearNumero = (n: number): string => numero.format(n);

export function haceCuanto(iso: string): string {
  const segundos = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
  if (segundos < 60) return `hace ${segundos} s`;
  const minutos = Math.round(segundos / 60);
  if (minutos < 60) return `hace ${minutos} min`;
  const horas = Math.round(minutos / 60);
  if (horas < 48) return `hace ${horas} h`;
  return formatearFechaHora(iso);
}
