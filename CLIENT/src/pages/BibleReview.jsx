// =============================================================================
// BibleReview.jsx - BIBLIA EDITABLE CON GUARDADO REAL
// =============================================================================

import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { bibleAPI } from '../services/api';

export default function BibleReview() {
  const { id: projectId } = useParams();
  const navigate = useNavigate();
  
  const [bible, setBible] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [saveMessage, setSaveMessage] = useState(null);
  const [expandedSections, setExpandedSections] = useState({
    identidad: true,
    personajes: true,
    voz: true,
    noCorregir: true,
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

  // Actualizar un campo simple
  function updateField(path, value) {
    setBible(prev => {
      const newBible = JSON.parse(JSON.stringify(prev));
      const keys = path.split('.');
      let obj = newBible;
      for (let i = 0; i < keys.length - 1; i++) {
        if (!obj[keys[i]]) obj[keys[i]] = {};
        obj = obj[keys[i]];
      }
      obj[keys[keys.length - 1]] = value;
      return newBible;
    });
    setHasChanges(true);
    setSaveMessage(null);
  }

  // Actualizar un item en un array
  function updateArrayItem(path, index, value) {
    setBible(prev => {
      const newBible = JSON.parse(JSON.stringify(prev));
      const keys = path.split('.');
      let obj = newBible;
      for (const key of keys) {
        if (!obj[key]) obj[key] = [];
        obj = obj[key];
      }
      if (Array.isArray(obj)) {
        obj[index] = value;
      }
      return newBible;
    });
    setHasChanges(true);
    setSaveMessage(null);
  }

  // Agregar item a un array
  function addArrayItem(path, defaultValue = '') {
    setBible(prev => {
      const newBible = JSON.parse(JSON.stringify(prev));
      const keys = path.split('.');
      let obj = newBible;
      for (let i = 0; i < keys.length - 1; i++) {
        if (!obj[keys[i]]) obj[keys[i]] = {};
        obj = obj[keys[i]];
      }
      const lastKey = keys[keys.length - 1];
      if (!obj[lastKey]) obj[lastKey] = [];
      obj[lastKey].push(defaultValue);
      return newBible;
    });
    setHasChanges(true);
  }

  // Eliminar item de un array
  function removeArrayItem(path, index) {
    setBible(prev => {
      const newBible = JSON.parse(JSON.stringify(prev));
      const keys = path.split('.');
      let obj = newBible;
      for (let i = 0; i < keys.length - 1; i++) {
        obj = obj[keys[i]];
      }
      const lastKey = keys[keys.length - 1];
      if (Array.isArray(obj[lastKey])) {
        obj[lastKey].splice(index, 1);
      }
      return newBible;
    });
    setHasChanges(true);
  }

  // GUARDAR CAMBIOS - Conectado a la API real
  async function handleSave() {
    try {
      setIsSaving(true);
      setSaveMessage(null);
      await bibleAPI.save(projectId, bible);
      setHasChanges(false);
      setSaveMessage({ type: 'success', text: '✓ Cambios guardados' });
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (err) {
      setSaveMessage({ type: 'error', text: 'Error: ' + err.message });
    } finally {
      setIsSaving(false);
    }
  }

  // APROBAR Y CONTINUAR
  async function handleApprove() {
    try {
      // Si hay cambios sin guardar, guardar primero
      if (hasChanges) {
        await bibleAPI.save(projectId, bible);
      }
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
        <Link to="/" className="btn btn-outline" style={{ marginTop: '1rem' }}>
          ← Volver al Dashboard
        </Link>
      </div>
    );
  }

  if (!bible) return null;

  const inputStyle = {
    width: '100%',
    padding: '0.5rem',
    border: '1px solid var(--color-border)',
    marginTop: '0.25rem',
    fontSize: '0.875rem',
    fontFamily: 'monospace'
  };

  const textareaStyle = {
    ...inputStyle,
    minHeight: '80px',
    resize: 'vertical'
  };

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
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            {saveMessage && (
              <span style={{ 
                fontSize: '0.875rem',
                color: saveMessage.type === 'success' ? '#059669' : '#B91C1C'
              }}>
                {saveMessage.text}
              </span>
            )}
            <button 
              className="btn btn-outline"
              onClick={handleSave}
              disabled={!hasChanges || isSaving}
              style={{ opacity: hasChanges ? 1 : 0.5 }}
            >
              {isSaving ? 'Guardando...' : 'Guardar'}
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
                style={inputStyle}
              />
            </div>
            <div>
              <label className="label">Subgénero</label>
              <input
                type="text"
                value={bible.identidad_obra?.subgenero || ''}
                onChange={(e) => updateField('identidad_obra.subgenero', e.target.value)}
                style={inputStyle}
              />
            </div>
            <div>
              <label className="label">Tono Predominante</label>
              <input
                type="text"
                value={bible.identidad_obra?.tono_predominante || ''}
                onChange={(e) => updateField('identidad_obra.tono_predominante', e.target.value)}
                style={inputStyle}
              />
            </div>
            <div>
              <label className="label">Estilo Narrativo</label>
              <input
                type="text"
                value={bible.identidad_obra?.estilo_narrativo || ''}
                onChange={(e) => updateField('identidad_obra.estilo_narrativo', e.target.value)}
                style={inputStyle}
              />
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <label className="label">Tema Central</label>
              <textarea
                value={bible.identidad_obra?.tema_central || ''}
                onChange={(e) => updateField('identidad_obra.tema_central', e.target.value)}
                style={textareaStyle}
              />
            </div>
          </div>
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
              <textarea
                value={bible.voz_del_autor?.estilo_detectado || ''}
                onChange={(e) => updateField('voz_del_autor.estilo_detectado', e.target.value)}
                style={textareaStyle}
              />
            </div>
            
            <div style={{ marginBottom: '1.5rem' }}>
              <label className="label">Recursos Distintivos</label>
              {bible.voz_del_autor?.recursos_distintivos?.map((recurso, idx) => (
                <div key={idx} style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                  <input
                    type="text"
                    value={recurso}
                    onChange={(e) => updateArrayItem('voz_del_autor.recursos_distintivos', idx, e.target.value)}
                    style={{ ...inputStyle, marginTop: 0 }}
                  />
                  <button 
                    onClick={() => removeArrayItem('voz_del_autor.recursos_distintivos', idx)}
                    className="btn"
                    style={{ background: '#FEE2E2', color: '#B91C1C', padding: '0.25rem 0.5rem' }}
                  >
                    ✕
                  </button>
                </div>
              ))}
              <button 
                onClick={() => addArrayItem('voz_del_autor.recursos_distintivos', '')}
                className="btn btn-outline"
                style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}
              >
                + Agregar recurso
              </button>
            </div>
          </>
        )}
      </section>

      {/* NO CORREGIR - CRÍTICO */}
      <section className="content-section" style={{ borderColor: '#F59E0B', background: '#FFFBEB' }}>
        <button 
          className="title-section" 
          onClick={() => toggleSection('noCorregir')}
          style={{ 
            width: '100%', 
            textAlign: 'left', 
            background: 'none', 
            cursor: 'pointer',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            color: '#92400E',
            borderColor: '#F59E0B'
          }}
        >
          <span>⚠️ ELEMENTOS A PRESERVAR (NO CORREGIR)</span>
          <span style={{ fontSize: '0.875rem' }}>{expandedSections.noCorregir ? '−' : '+'}</span>
        </button>
        
        {expandedSections.noCorregir && (
          <div style={{ marginTop: '1rem' }}>
            <p className="meta" style={{ marginBottom: '1rem', color: '#92400E' }}>
              Estos elementos serán respetados durante la edición. Agrega cualquier uso intencional 
              de lenguaje, regionalismos, o decisiones estilísticas que no deben modificarse.
            </p>
            
            {bible.voz_del_autor?.NO_CORREGIR?.map((item, idx) => (
              <div key={idx} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <input
                  type="text"
                  value={item}
                  onChange={(e) => updateArrayItem('voz_del_autor.NO_CORREGIR', idx, e.target.value)}
                  style={{ ...inputStyle, marginTop: 0, background: 'white' }}
                  placeholder="Ej: Uso de 'piel morena' (intencional)"
                />
                <button 
                  onClick={() => removeArrayItem('voz_del_autor.NO_CORREGIR', idx)}
                  className="btn"
                  style={{ background: '#FEE2E2', color: '#B91C1C', padding: '0.25rem 0.5rem' }}
                >
                  ✕
                </button>
              </div>
            ))}
            
            <button 
              onClick={() => addArrayItem('voz_del_autor.NO_CORREGIR', '')}
              className="btn"
              style={{ 
                marginTop: '0.5rem', 
                fontSize: '0.875rem',
                background: '#FEF3C7',
                color: '#92400E',
                border: '1px solid #F59E0B'
              }}
            >
              + Agregar elemento a preservar
            </button>
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
                <input
                  type="text"
                  value={char.nombre || ''}
                  onChange={(e) => {
                    const newChar = { ...char, nombre: e.target.value };
                    setBible(prev => {
                      const newBible = JSON.parse(JSON.stringify(prev));
                      newBible.reparto_completo.protagonistas[idx] = newChar;
                      return newBible;
                    });
                    setHasChanges(true);
                  }}
                  style={{ ...inputStyle, fontWeight: 700, marginBottom: '0.5rem' }}
                />
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
          <button 
            className="btn btn-outline" 
            onClick={handleSave}
            disabled={!hasChanges || isSaving}
          >
            {isSaving ? 'Guardando...' : 'Guardar'}
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