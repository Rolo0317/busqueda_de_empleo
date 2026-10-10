import { useCallback, useState } from 'react';
import { BotPanel } from './components/BotPanel';
import { JobsTable } from './components/JobsTable';
import { LoginForm } from './components/LoginForm';
import { Overview } from './components/Overview';
import { Seguimiento } from './components/Seguimiento';
import { useSession } from './hooks/useSession';
import './App.css';

export default function App() {
  const { estado, correo, entrar, salir } = useSession();
  // Sube cada vez que termina una corrida: resumen, grafica y listado se recargan.
  const [version, setVersion] = useState(0);
  const alTerminarCorrida = useCallback(() => setVersion((v) => v + 1), []);

  if (estado === 'comprobando') {
    return <main className="pantalla"><p className="apoyo">Comprobando sesión…</p></main>;
  }

  if (estado === 'anonimo') {
    return <main className="pantalla"><LoginForm onEntrar={entrar} /></main>;
  }

  if (estado === 'sin-permiso') {
    return (
      <main className="pantalla">
        <section className="tarjeta">
          <h1>Sin acceso</h1>
          <p className="apoyo">La cuenta {correo} no está autorizada para operar el bot.</p>
          <button type="button" className="secundario" onClick={() => void salir()}>Salir</button>
        </section>
      </main>
    );
  }

  return (
    <main className="pantalla ancho">
      <header className="barra">
        <h1>Panel de postulación</h1>
        <div className="sesion">
          <a href="/" className="enlace">Hoja de vida</a>
          <span>{correo}</span>
          <button type="button" onClick={() => void salir()} className="secundario">Salir</button>
        </div>
      </header>
      <BotPanel onCorridaTerminada={alTerminarCorrida} />
      <Seguimiento version={version} />
      <Overview version={version} />
      <JobsTable version={version} />
    </main>
  );
}
