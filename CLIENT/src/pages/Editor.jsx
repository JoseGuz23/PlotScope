// =============================================================================
// Editor.jsx - EDITOR DE MANUSCRITO (PROFESIONAL)
// =============================================================================

import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { manuscriptAPI } from '../services/api';

export default function Editor() {
  const { id: projectId } = useParams();
  
  const [content, setContent] = useState('');
  const [annotatedContent, setAnnotatedContent] = useState('');
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('annotated');

  useEffect(() => {
    loadContent();
  }, [projectId]);

  async function loadContent() {
    try {
      setIsLoading(true);
      
      const [edited, annotated, summaryData] = await Promise.all([
        manuscriptAPI.getEdited(projectId).catch(() => ''),
        manuscriptAPI.getAnnotated(projectId).catch(() => ''),
        manuscriptAPI.getSummary(projectId).catch(() => null),
      ]);
      
      setContent(edited);
      setAnnotatedContent(annotated);
      setSummary(summaryData);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 0' }}>
        <div className="status-indicator" style={{ justifyContent: 'center' }}>
          <div className="status-dot"></div>
          <span className="status-text">Cargando editor...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="content-section" style={{ borderColor: '#FCA5A5', background: '#FEF2F2' }}>
        <h2 className="title-section" style={{ color: '#B91C1C', borderColor: '#FCA5A5' }}>
          Error al Cargar
        </h2>
        <p style={{ color: '#B91C1C' }}>{error}</p>
        <Link to="/" className="btn btn-outline" style={{ marginTop: '1rem' }}>
          ← Volver al Dashboard
        </Link>
      </div>
    );
  }

  return (
    <>
      {/* HEADER */}
      <header className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <Link to="/" className="meta" style={{ display: 'block', marginBottom: '0.5rem' }}>
              ← Volver al Dashboard
            </Link>
            <h1 className="title-main">EDITOR DE MANUSCRITO</h1>
            {summary && (
              <p className="page-header-meta">
                {summary.book_name} | {summary.estadisticas?.total_words?.toLocaleString()} palabras | {summary.estadisticas?.total_changes} cambios
              </p>
            )}
          </div>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            {summary?.urls?.manuscrito_limpio && (
              <a 
                href={summary.urls.manuscrito_limpio} 
                target="_blank" 
                rel="noopener noreferrer"
                className="btn btn-outline"
              >
                Descargar Limpio
              </a>
            )}
            {summary?.urls?.manuscrito_anotado && (
              <a 
                href={summary.urls.manuscrito_anotado} 
                target="_blank" 
                rel="noopener noreferrer"
                className="btn btn-primary"
              >
                Descargar Anotado
              </a>
            )}
          </div>
        </div>
      </header>

      {/* STATS */}
      {summary && (
        <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(5, 1fr)' }}>
          <div className="stat-card">
            <p className="label">Capítulos</p>
            <p className="stat-value" style={{ fontSize: '1.5rem' }}>{summary.capitulos_procesados}</p>
          </div>
          <div className="stat-card">
            <p className="label">Cambios</p>
            <p className="stat-value text-primary" style={{ fontSize: '1.5rem' }}>
              {summary.estadisticas?.total_changes}
            </p>
          </div>
          <div className="stat-card">
            <p className="label">Costo</p>
            <p className="stat-value" style={{ fontSize: '1.5rem', color: '#059669' }}>
              ${summary.estadisticas?.total_cost_usd?.toFixed(2)}
            </p>
          </div>
          <div className="stat-card">
            <p className="label">Tiempo</p>
            <p className="mono" style={{ fontSize: '1rem', fontWeight: 700, marginTop: '0.5rem' }}>
              {summary.tiempos?.total?.split('.')[0] || '—'}
            </p>
          </div>
          <div className="stat-card">
            <p className="label">Versión</p>
            <p className="mono" style={{ fontSize: '1rem', fontWeight: 700, marginTop: '0.5rem' }}>
              {summary.version}
            </p>
          </div>
        </div>
      )}

      {/* VIEW MODE SELECTOR */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <button
          onClick={() => setViewMode('annotated')}
          className={viewMode === 'annotated' ? 'btn btn-primary' : 'btn btn-outline'}
        >
          Vista Anotada
        </button>
        <button
          onClick={() => setViewMode('clean')}
          className={viewMode === 'clean' ? 'btn btn-primary' : 'btn btn-outline'}
        >
          Vista Limpia
        </button>
      </div>

      {/* EDITOR AREA */}
      <section className="content-section">
        {/* Toolbar */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          borderBottom: '1px solid var(--color-border)',
          paddingBottom: '1rem',
          marginBottom: '1.5rem'
        }}>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn btn-outline" title="Cambio anterior">← Anterior</button>
            <button className="btn btn-outline" title="Cambio siguiente">Siguiente →</button>
            <span className="meta" style={{ alignSelf: 'center', marginLeft: '0.5rem' }}>
              Navegación de cambios (próximamente)
            </span>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn" style={{ background: '#D1FAE5', color: '#065F46' }}>
              ✓ Aceptar Todo
            </button>
            <button className="btn" style={{ background: '#FEE2E2', color: '#B91C1C' }}>
              ✗ Rechazar Todo
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="content-body" style={{ maxHeight: '600px', overflowY: 'auto' }}>
          {viewMode === 'annotated' ? annotatedContent : content}
        </div>
      </section>

      {/* INFO BOX */}
      <div style={{ 
        background: '#EFF6FF', 
        border: '1px solid #BFDBFE', 
        padding: '1rem',
        marginTop: '1.5rem'
      }}>
        <p className="label" style={{ color: '#1E40AF', marginBottom: '0.5rem' }}>
          🚧 Editor Interactivo en Desarrollo
        </p>
        <p className="mono" style={{ fontSize: '0.875rem', color: '#1E40AF' }}>
          La siguiente versión incluirá el editor TipTap con track changes interactivo: 
          aceptar/rechazar cambios individuales, navegación entre cambios, y export final.
        </p>
      </div>

      {/* FILE LINKS */}
      {summary?.urls && (
        <section className="content-section" style={{ marginTop: '1.5rem' }}>
          <h2 className="title-section">📎 ARCHIVOS GENERADOS</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
            {Object.entries(summary.urls).map(([key, url]) => (
              <a
                key={key}
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="project-link mono"
                style={{ fontSize: '0.875rem' }}
              >
                {key.replace(/_/g, ' ')} →
              </a>
            ))}
          </div>
        </section>
      )}
    </>
  );
}
