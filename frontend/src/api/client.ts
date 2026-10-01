/** Cliente HTTP unico. Todo lo que hable con la API pasa por aqui. */

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

function leerCookie(nombre: string): string | null {
  const encontrada = document.cookie
    .split(';')
    .map((c) => c.trim())
    .find((c) => c.startsWith(`${nombre}=`));
  return encontrada ? decodeURIComponent(encontrada.slice(nombre.length + 1)) : null;
}

/** Django exige el token CSRF en cada peticion que modifica estado. */
export async function asegurarCsrf(): Promise<void> {
  if (leerCookie('csrftoken') === null) {
    await fetch('/api/auth/csrf/', { credentials: 'include' });
  }
}

interface Opciones {
  metodo?: 'GET' | 'POST';
  cuerpo?: unknown;
}

export async function peticion<T>(ruta: string, opciones: Opciones = {}): Promise<T> {
  const { metodo = 'GET', cuerpo } = opciones;
  const cabeceras: Record<string, string> = {};

  if (metodo !== 'GET') {
    await asegurarCsrf();
    const token = leerCookie('csrftoken');
    if (token !== null) cabeceras['X-CSRFToken'] = token;
    cabeceras['Content-Type'] = 'application/json';
  }

  const respuesta = await fetch(ruta, {
    method: metodo,
    credentials: 'include',
    headers: cabeceras,
    body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
  });

  if (respuesta.status === 204) return undefined as T;

  const datos: unknown = await respuesta.json().catch(() => null);

  if (!respuesta.ok) {
    const detalle =
      datos !== null && typeof datos === 'object' && 'detail' in datos
        ? String((datos as { detail: unknown }).detail)
        : `Error ${respuesta.status}`;
    throw new ApiError(respuesta.status, detalle);
  }

  return datos as T;
}
