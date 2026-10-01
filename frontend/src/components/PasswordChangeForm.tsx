import { useState, type FormEvent } from 'react';
import { cambiarPassword } from '../api/auth';

const LARGO_MINIMO = 12;

interface Props {
  onCambiada: () => void;
}

export function PasswordChangeForm({ onCambiada }: Props) {
  const [actual, setActual] = useState('');
  const [nueva, setNueva] = useState('');
  const [repetida, setRepetida] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function manejarEnvio(evento: FormEvent) {
    evento.preventDefault();
    setError(null);

    // Se comprueba aqui lo que el usuario puede corregir sin ir al servidor;
    // la validacion de fondo la sigue haciendo Django.
    if (nueva !== repetida) {
      setError('Las dos contraseñas nuevas no coinciden.');
      return;
    }

    setEnviando(true);
    try {
      await cambiarPassword(actual, nueva);
      onCambiada();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo cambiar la contraseña');
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="tarjeta" onSubmit={manejarEnvio}>
      <h1>Cambia tu contraseña</h1>
      <p className="apoyo">
        Tu cuenta se creó con una clave temporal que otra persona conoce. Hasta que la
        cambies, el bot no puede ejecutarse.
      </p>

      <label>
        Contraseña temporal
        <input
          type="password"
          value={actual}
          onChange={(e) => setActual(e.target.value)}
          autoComplete="current-password"
          required
        />
      </label>

      <label>
        Contraseña nueva
        <input
          type="password"
          value={nueva}
          onChange={(e) => setNueva(e.target.value)}
          autoComplete="new-password"
          minLength={LARGO_MINIMO}
          required
        />
      </label>

      <label>
        Repite la nueva
        <input
          type="password"
          value={repetida}
          onChange={(e) => setRepetida(e.target.value)}
          autoComplete="new-password"
          minLength={LARGO_MINIMO}
          required
        />
      </label>

      <p className="apoyo">Mínimo {LARGO_MINIMO} caracteres. No puede ser solo números ni una clave común.</p>

      {error !== null && <p className="error" role="alert">{error}</p>}

      <button type="submit" disabled={enviando}>
        {enviando ? 'Guardando…' : 'Cambiar contraseña'}
      </button>
    </form>
  );
}
