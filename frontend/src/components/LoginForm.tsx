import { useState, type FormEvent } from 'react';

interface Props {
  onEntrar: (usuario: string, password: string) => Promise<void>;
}

export function LoginForm({ onEntrar }: Props) {
  const [usuario, setUsuario] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function manejarEnvio(evento: FormEvent) {
    evento.preventDefault();
    setError(null);
    setEnviando(true);
    try {
      await onEntrar(usuario, password);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo iniciar sesión');
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="tarjeta login" onSubmit={manejarEnvio}>
      <h1>Panel de postulación</h1>
      <p className="apoyo">Este panel dispara postulaciones reales. Requiere sesión.</p>

      <label>
        Usuario
        <input
          value={usuario}
          onChange={(e) => setUsuario(e.target.value)}
          autoComplete="username"
          required
        />
      </label>

      <label>
        Contraseña
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
        />
      </label>

      {error !== null && <p className="error" role="alert">{error}</p>}

      <button type="submit" disabled={enviando}>
        {enviando ? 'Entrando…' : 'Entrar'}
      </button>
    </form>
  );
}
