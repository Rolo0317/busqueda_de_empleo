import { BotPanel } from './components/BotPanel';
import { JobsTable } from './components/JobsTable';
import { LoginForm } from './components/LoginForm';
import { PasswordChangeForm } from './components/PasswordChangeForm';
import { useSession } from './hooks/useSession';
import './App.css';

export default function App() {
  const { estado, usuario, entrar, salir, marcarPasswordCambiada } = useSession();

  if (estado === 'comprobando') {
    return <main className="pantalla"><p className="apoyo">Comprobando sesión…</p></main>;
  }

  if (estado === 'anonimo') {
    return <main className="pantalla"><LoginForm onEntrar={entrar} /></main>;
  }

  // La clave temporal bloquea todo lo demas: no es un aviso que se pueda saltar.
  if (usuario?.debeCambiarPassword === true) {
    return (
      <main className="pantalla">
        <PasswordChangeForm onCambiada={marcarPasswordCambiada} />
        <button onClick={() => void salir()} className="secundario">Salir</button>
      </main>
    );
  }

  return (
    <main className="pantalla ancho">
      <header className="barra">
        <h1>Panel de postulación</h1>
        <div className="sesion">
          <span>{usuario?.usuario}</span>
          <button onClick={() => void salir()} className="secundario">Salir</button>
        </div>
      </header>
      <BotPanel />
      <JobsTable />
    </main>
  );
}
