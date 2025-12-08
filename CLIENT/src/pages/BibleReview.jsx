// =============================================================================
// BibleReview.jsx - REVISAR BIBLIA NARRATIVA (PROFESIONAL)
// =============================================================================

import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { bibleAPI } from '../services/api';

export default function BibleReview() {
  const { id: projectId } = useParams();
  const navigate = useNavigate();
  
  const [bible, setBible] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [expandedSections, setExpandedSections] = useState({
    identidad: true,
    personajes: true,
    voz: true,
    metricas: false,
  });

  useEffect(() => {
    loadBible();
  }, [projectId]);

  async function loadBible() {
    try {
      setIsLoading(true);
      const data = await bibleAPI.get(projectId);
      setBible(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  function toggleSection(section) {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  }

  function updateField(path, value) {
    setBible(prev => {
      const newBible = JSON.parse(JSON.stringify(prev));
      const keys = path.split('.');
      let obj = newBible;
      for (let i = 0; i < keys.length - 1; i++) {
        obj = obj[keys[i]];
      }
      obj[keys[keys.length - 1]] = value;
      return newBible;
    });
    setHasChanges(true);
  }

  async function handleApprove() {
    try {
      await bibleAPI.approve(projectId);
      navigate(`/proyecto/${projectId}/editor`);
    } catch (err) {
      alert('Error: ' + err.message);
    }
  }

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 0' }}>
        <div className="status-indicator" style={{ justifyContent: 'center' }}>
          <div className="status-dot"></div>
          <span className="status-text">Cargando biblia narrativa...</span>
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
        <p className="meta" style={{ marginTop: '1rem' }}>
          Verifica que CORS esté configurado en tu Azure Storage Account.
        </p>
        <Link to="/" className="btn btn-outline" style={{ marginTop: '1rem' }}>
          ← Volver al Dashboard
        </Link>
      </div>
    );
  }

  if (!bible) return null;

  return (
    <>
      {/* HEADER */}
      <header className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <Link to="/" className="meta" style={{ display: 'block', marginBottom: '0.5rem' }}>
              ← Volver al Dashboard
            </Link>
            <h1 className="title-main">BIBLIA NARRATIVA</h1>
            <p className="page-header-meta">
              Revisa y ajusta el análisis de tu obra antes de continuar con la edición
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button 
              className="btn btn-outline"
              disabled={!hasChanges}
              style={{ opacity: hasChanges ? 1 : 0.5 }}
            >
              Guardar
            </button>
            <button className="btn btn-primary" onClick={handleApprove}>
              Aprobar y Continuar →
            </button>
          </div>
        </div>
      </header>

      {/* Warning si hay cambios */}
      {hasChanges && (
        <div style={{ 
          background: '#FEF3C7', 
          border: '1px solid #F59E0B', 
          padding: '0.75rem 1rem',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          <span style={{ fontSize: '1rem' }}>⚠️</span>
          <span className="mono" style={{ fontSize: '0.875rem', color: '#92400E', fontWeight: 600 }}>
            Tienes cambios sin guardar
          </span>
        </div>
      )}

      {/* IDENTIDAD DE LA OBRA */}
      <section className="content-section">
        <button 
          className="title-section" 
          onClick={() => toggleSection('identidad')}
          style={{ 
            width: '100%', 
            textAlign: 'left', 
            background: 'none', 
            cursor: 'pointer',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <span>📚 IDENTIDAD DE LA OBRA</span>
          <span style={{ fontSize: '0.875rem' }}>{expandedSections.identidad ? '−' : '+'}</span>
        </button>
        
        {expandedSections.identidad && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            <div>
              <label className="label">Género</label>
              <input
                type="text"
                value={bible.identidad_obra?.genero || ''}
                onChange={(e) => updateField('identidad_obra.genero', e.target.value)}
                className="mono"
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid var(--color-border)',
                  marginTop: '0.25rem',
                  fontSize: '0.875rem'
                }}
              />
            </div>
            <div>
              <label className="label">Subgénero</label>
              <input
                type="text"
                value={bible.identidad_obra?.subgenero || ''}
                onChange={(e) => updateField('identidad_obra.subgenero', e.target.value)}
                className="mono"
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid var(--color-border)',
                  marginTop: '0.25rem',
                  fontSize: '0.875rem'
                }}
              />
            </div>
            <div>
              <label className="label">Tono Predominante</label>
              <input
                type="text"
                value={bible.identidad_obra?.tono_predominante || ''}
                onChange={(e) => updateField('identidad_obra.tono_predominante', e.target.value)}
                className="mono"
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid var(--color-border)',
                  marginTop: '0.25rem',
                  fontSize: '0.875rem'
                }}
              />
            </div>
            <div>
              <label className="label">Estilo Narrativo</label>
              <input
                type="text"
                value={bible.identidad_obra?.estilo_narrativo || ''}
                onChange={(e) => updateField('identidad_obra.estilo_narrativo', e.target.value)}
                className="mono"
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid var(--color-border)',
                  marginTop: '0.25rem',
                  fontSize: '0.875rem'
                }}
              />
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <label className="label">Tema Central</label>
              <textarea
                value={bible.identidad_obra?.tema_central || ''}
                onChange={(e) => updateField('identidad_obra.tema_central', e.target.value)}
                className="mono"
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid var(--color-border)',
                  marginTop: '0.25rem',
                  fontSize: '0.875rem',
                  minHeight: '80px',
                  resize: 'vertical'
                }}
              />
            </div>
          </div>
        )}
      </section>

      {/* PERSONAJES */}
      <section className="content-section">
        <button 
          className="title-section" 
          onClick={() => toggleSection('personajes')}
          style={{ 
            width: '100%', 
            textAlign: 'left', 
            background: 'none', 
            cursor: 'pointer',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <span>👥 REPARTO DE PERSONAJES</span>
          <span style={{ fontSize: '0.875rem' }}>{expandedSections.personajes ? '−' : '+'}</span>
        </button>
        
        {expandedSections.personajes && (
          <>
            {/* Protagonistas */}
            <h4 className="label" style={{ color: 'var(--color-primary)', marginBottom: '1rem' }}>
              PROTAGONISTAS
            </h4>
            {bible.reparto_completo?.protagonistas?.map((char, idx) => (
              <div key={idx} style={{ 
                background: '#F0FDF4', 
                border: '1px solid #BBF7D0', 
                padding: '1rem',
                marginBottom: '1rem'
              }}>
                <div style={{ fontWeight: 700, fontSize: '1rem', marginBottom: '0.5rem' }}>
                  {char.nombre}
                </div>
                <div className="meta">
                  <strong>Arquetipo:</strong> {char.rol_arquetipo}<br/>
                  <strong>Motivación:</strong> {char.motivacion_principal}<br/>
                  <strong>Arco:</strong> {char.arco_personaje}
                </div>
              </div>
            ))}

            {/* Antagonistas */}
            <h4 className="label" style={{ color: '#B91C1C', marginBottom: '1rem', marginTop: '1.5rem' }}>
              ANTAGONISTAS
            </h4>
            {bible.reparto_completo?.antagonistas?.map((char, idx) => (
              <div key={idx} style={{ 
                background: '#FEF2F2', 
                border: '1px solid #FECACA', 
                padding: '1rem',
                marginBottom: '1rem'
              }}>
                <div style={{ fontWeight: 700, fontSize: '1rem', marginBottom: '0.5rem' }}>
                  {char.nombre}
                </div>
                <div className="meta">
                  <strong>Arquetipo:</strong> {char.rol_arquetipo}<br/>
                  <strong>Motivación:</strong> {char.motivacion_principal}
                </div>
              </div>
            ))}

            {/* Secundarios */}
            {bible.reparto_completo?.secundarios?.length > 0 && (
              <>
                <h4 className="label" style={{ marginBottom: '1rem', marginTop: '1.5rem' }}>
                  SECUNDARIOS
                </h4>
                {bible.reparto_completo.secundarios.map((char, idx) => (
                  <div key={idx} style={{ 
                    background: '#F9FAFB', 
                    border: '1px solid var(--color-border)', 
                    padding: '1rem',
                    marginBottom: '1rem'
                  }}>
                    <div style={{ fontWeight: 700, fontSize: '1rem', marginBottom: '0.5rem' }}>
                      {char.nombre}
                    </div>
                    <div className="meta">
                      <strong>Rol:</strong> {char.rol_arquetipo}
                    </div>
                  </div>
                ))}
              </>
            )}
          </>
        )}
      </section>

      {/* VOZ DEL AUTOR */}
      <section className="content-section">
        <button 
          className="title-section" 
          onClick={() => toggleSection('voz')}
          style={{ 
            width: '100%', 
            textAlign: 'left', 
            background: 'none', 
            cursor: 'pointer',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <span>✍️ VOZ DEL AUTOR</span>
          <span style={{ fontSize: '0.875rem' }}>{expandedSections.voz ? '−' : '+'}</span>
        </button>
        
        {expandedSections.voz && (
          <>
            <div style={{ marginBottom: '1.5rem' }}>
              <label className="label">Estilo Detectado</label>
              <p className="mono" style={{ marginTop: '0.25rem' }}>
                {bible.voz_del_autor?.estilo_detectado}
              </p>
            </div>
            
            <div style={{ marginBottom: '1.5rem' }}>
              <label className="label">Recursos Distintivos</label>
              <ul style={{ marginTop: '0.5rem', paddingLeft: '1.25rem' }}>
                {bible.voz_del_autor?.recursos_distintivos?.map((r, i) => (
                  <li key={i} className="mono" style={{ fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                    {r}
                  </li>
                ))}
              </ul>
            </div>

            <div style={{ 
              background: '#FEF3C7', 
              border: '1px solid #F59E0B', 
              padding: '1rem'
            }}>
              <label className="label" style={{ color: '#92400E' }}>
                ⚠️ NO CORREGIR (Elementos intencionales)
              </label>
              <ul style={{ marginTop: '0.5rem', paddingLeft: '1.25rem' }}>
                {bible.voz_del_autor?.NO_CORREGIR?.map((item, i) => (
                  <li key={i} className="mono" style={{ fontSize: '0.875rem', marginBottom: '0.25rem', color: '#92400E' }}>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}
      </section>

      {/* MÉTRICAS */}
      <section className="content-section">
        <button 
          className="title-section" 
          onClick={() => toggleSection('metricas')}
          style={{ 
            width: '100%', 
            textAlign: 'left', 
            background: 'none', 
            cursor: 'pointer',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <span>📊 MÉTRICAS GLOBALES</span>
          <span style={{ fontSize: '0.875rem' }}>{expandedSections.metricas ? '−' : '+'}</span>
        </button>
        
        {expandedSections.metricas && (
          <div className="stats-grid" style={{ marginTop: '1rem' }}>
            <div className="stat-card">
              <p className="label">Palabras</p>
              <p className="stat-value" style={{ fontSize: '1.5rem' }}>
                {bible.metricas_globales?.total_palabras?.toLocaleString()}
              </p>
            </div>
            <div className="stat-card">
              <p className="label">Capítulos</p>
              <p className="stat-value" style={{ fontSize: '1.5rem' }}>
                {bible.metricas_globales?.total_capitulos}
              </p>
            </div>
            <div className="stat-card">
              <p className="label">Score Global</p>
              <p className="stat-value text-primary" style={{ fontSize: '1.5rem' }}>
                {bible.metricas_globales?.score_global}
              </p>
            </div>
            <div className="stat-card">
              <p className="label">Coherencia</p>
              <p className="stat-value" style={{ fontSize: '1.5rem', color: '#059669' }}>
                {bible.metricas_globales?.score_coherencia_personajes}
              </p>
            </div>
          </div>
        )}
      </section>

      {/* Bottom action bar */}
      <div style={{ 
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        background: 'var(--color-surface)',
        borderTop: '1px solid var(--color-border)',
        padding: '1rem 2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span className="mono" style={{ fontSize: '0.875rem', color: 'var(--color-subtle)' }}>
          {hasChanges ? '⚠️ Cambios sin guardar' : '✓ Todo guardado'}
        </span>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-outline" disabled={!hasChanges}>
            Guardar
          </button>
          <button className="btn btn-primary" onClick={handleApprove}>
            Aprobar y Continuar al Editor →
          </button>
        </div>
      </div>

      {/* Spacer for fixed bottom bar */}
      <div style={{ height: '80px' }}></div>
    </>
  );
}
