import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// El panel se publica en /panel/ del mismo sitio que la hoja de vida (Vercel).
// Ya no hay backend propio: el navegador habla directo con Supabase.
export default defineConfig({
  base: '/panel/',
  plugins: [react()],
  server: { port: 5173 },
});
