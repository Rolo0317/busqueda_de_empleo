import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// El 8000 suele estar ocupado por otro proyecto Django de esta maquina, asi que
// este backend vive en el 8001. Se puede cambiar con VITE_API_TARGET.
const PUERTO_BACKEND_POR_DEFECTO = 'http://127.0.0.1:8001';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        // El proxy hace que front y API compartan origen: la cookie de sesion
        // de Django viaja sin configurar CORS ni relajar SameSite.
        '/api': {
          target: env.VITE_API_TARGET || PUERTO_BACKEND_POR_DEFECTO,
          changeOrigin: true,
        },
      },
    },
  };
});
