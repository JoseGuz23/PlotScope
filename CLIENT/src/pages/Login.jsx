// =============================================================================
// Login.jsx - PÁGINA DE LOGIN
// =============================================================================

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
      await authAPI.login(password);
      navigate('/');
    } catch (err) {
      setError(err.message || 'Contraseña incorrecta');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--color-bg)',
      padding: '2rem',
    }}>
      <div style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        padding: '3rem',
        width: '100%',
        maxWidth: '400px',
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{
            fontFamily: 'var(--font-serif)',
            fontSize: '2.5rem',
            fontWeight: 800,
            margin: 0,
          }}>
            LYA
          </h1>
          <p className="mono" style={{ color: 'var(--color-muted)', fontSize: '0.75rem' }}>
            v4.1.0 (Developmental Editor)
          </p>
        </div>

        {/* Título */}
        <h2 className="title-section" style={{ textAlign: 'center' }}>
          ACCESO RESTRINGIDO
        </h2>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1.5rem' }}>
            <label className="label" style={{ display: 'block', marginBottom: '0.5rem' }}>
              Contraseña
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Ingresa la contraseña"
              className="mono"
              autoFocus
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid var(--color-border)',
                fontSize: '1rem',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {/* Error */}
          {error && (
            <div style={{
              background: '#FEF2F2',
              border: '1px solid #FCA5A5',
              padding: '0.75rem',
              marginBottom: '1.5rem',
              color: '#B91C1C',
              fontSize: '0.875rem',
              textAlign: 'center',
            }}>
              ⚠️ {error}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            className="btn btn-primary"
            disabled={isLoading || !password}
            style={{
              width: '100%',
              padding: '0.875rem',
              fontSize: '0.875rem',
              opacity: (isLoading || !password) ? 0.6 : 1,
              cursor: (isLoading || !password) ? 'not-allowed' : 'pointer',
            }}
          >
            {isLoading ? 'Verificando...' : 'Entrar'}
          </button>
        </form>

        {/* Info */}
        <p className="mono" style={{
          marginTop: '2rem',
          fontSize: '0.75rem',
          color: 'var(--color-muted)',
          textAlign: 'center',
        }}>
          Sistema de edición literaria con IA.
          <br />
          Acceso solo para usuarios autorizados.
        </p>
      </div>
    </div>
  );
}
