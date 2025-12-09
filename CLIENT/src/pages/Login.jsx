import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../services/api';

export default function Login() {
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      // Intenta login contra el backend real
      await authAPI.login(password);
      navigate('/dashboard'); 
    } catch (err) {
      // Si falla (ej. contraseña mal), muestra el error SIN recargar
      console.error("Login fallido:", err);
      setError('La contraseña no es válida. Verifica tu variable de entorno SYLPHRENA_PASSWORD.');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-theme-bg px-4">
      
      <Link to="/" className="absolute top-8 left-8 text-sm font-extrabold text-gray-400 hover:text-theme-primary transition-colors tracking-wide">
        ← VOLVER A INICIO
      </Link>

      <div className="w-full max-w-md bg-white border-t-8 border-theme-primary shadow-2xl p-10 rounded-sm">
        
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="font-serif text-5xl font-bold text-theme-text mb-2">LYA</h1>
          <div className="h-1 w-16 bg-theme-primary mx-auto mb-4"></div>
          <p className="font-sans text-xs font-extrabold text-theme-subtle uppercase tracking-widest">
            Acceso Administrativo
          </p>
        </div>

        {/* Formulario */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-xs font-extrabold uppercase text-theme-subtle mb-2 tracking-wide">
              Llave de Acceso
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-4 border-2 border-gray-200 rounded-sm font-mono text-lg text-theme-text focus:border-theme-primary focus:outline-none transition-colors bg-gray-50 focus:bg-white placeholder-gray-300"
              placeholder="••••••••••••"
              autoFocus
            />
          </div>

          {/* Mensaje de Error Visible */}
          {error && (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 animate-pulse">
              <p className="text-sm text-red-800 font-bold">Acceso Denegado</p>
              <p className="text-xs text-red-600 mt-1 font-medium">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading || !password}
            className="w-full bg-theme-primary hover:bg-theme-primary-hover text-white font-extrabold py-4 px-4 rounded-sm shadow-lg transition-all transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed uppercase tracking-widest text-sm"
          >
            {isLoading ? 'Verificando...' : 'Ingresar al Sistema'}
          </button>
        </form>

        <div className="mt-8 text-center">
          <p className="font-mono text-[10px] text-gray-400">
            SECURE SYSTEM v4.3
          </p>
        </div>
      </div>
    </div>
  );
}