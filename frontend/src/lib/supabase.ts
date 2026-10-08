import { createClient } from '@supabase/supabase-js';

/**
 * Cliente unico de Supabase. La clave es la publicable: viaja al navegador por
 * diseno. Lo que protege los datos es que cada funcion empleo_* exige un
 * usuario operador, no que la clave sea secreta.
 */
const url = import.meta.env.VITE_SUPABASE_URL;
const clavePublica = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

if (!url || !clavePublica) {
  throw new Error('Faltan VITE_SUPABASE_URL o VITE_SUPABASE_PUBLISHABLE_KEY.');
}

export const supabase = createClient(url, clavePublica);
