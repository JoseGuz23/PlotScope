// =============================================================================
// Upload.jsx - SUBIR NUEVO MANUSCRITO (PROFESIONAL)
// =============================================================================

import { useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';

export default function Upload() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  
  const [file, setFile] = useState(null);
  const [projectName, setProjectName] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);

  function handleDragOver(e) {
    e.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave(e) {
    e.preventDefault();
    setIsDragging(false);
  }

  function handleDrop(e) {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    validateAndSetFile(droppedFile);
  }

  function handleFileSelect(e) {
    const selectedFile = e.target.files[0];
    validateAndSetFile(selectedFile);
  }

  function validateAndSetFile(f) {
    setError(null);
    if (!f) return;
    
    const ext = '.' + f.name.split('.').pop().toLowerCase();
    const allowed = ['.md', '.txt', '.docx'];
    
    if (!allowed.includes(ext)) {
      setError(`Formato no soportado. Usa: ${allowed.join(', ')}`);
      return;
    }
    
    if (f.size > 10 * 1024 * 1024) {
      setError('El archivo es muy grande. Máximo: 10MB');
      return;
    }
    
    setFile(f);
    if (!projectName) {
      setProjectName(f.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' '));
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    
    if (!file || !projectName.trim()) {
      setError('Selecciona un archivo y dale nombre al proyecto');
      return;
    }

    setIsUploading(true);
    
    // Simular upload
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    alert('¡Proyecto creado! (Demo - en producción iniciaría el procesamiento)');
    navigate('/');
  }

  return (
    <>
      {/* HEADER */}
      <header className="page-header">
        <Link to="/" className="meta" style={{ display: 'block', marginBottom: '0.5rem' }}>
          ← Volver al Dashboard
        </Link>
        <h1 className="title-main">NUEVO PROYECTO</h1>
        <p className="page-header-meta">
          Sube tu manuscrito para comenzar el análisis y edición con IA
        </p>
      </header>

      <div style={{ maxWidth: '600px' }}>
        <form onSubmit={handleSubmit}>
          {/* Nombre del proyecto */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label className="label" style={{ display: 'block', marginBottom: '0.5rem' }}>
              Nombre del Proyecto
            </label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="Ej: Mi Nueva Novela"
              className="mono"
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid var(--color-border)',
                fontSize: '0.875rem'
              }}
              required
            />
          </div>

          {/* Drop zone */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label className="label" style={{ display: 'block', marginBottom: '0.5rem' }}>
              Manuscrito
            </label>
            
            {!file ? (
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                style={{
                  border: `2px dashed ${isDragging ? 'var(--color-primary)' : 'var(--color-border)'}`,
                  background: isDragging ? 'rgba(15, 118, 110, 0.05)' : 'var(--color-surface)',
                  padding: '3rem 2rem',
                  textAlign: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>📄</div>
                <p style={{ fontWeight: 700, marginBottom: '0.5rem' }}>
                  Arrastra tu archivo aquí
                </p>
                <p className="meta" style={{ marginBottom: '1rem' }}>
                  o haz clic para seleccionar
                </p>
                <p className="meta" style={{ fontSize: '0.75rem', color: 'var(--color-muted)' }}>
                  Formatos: .md, .txt, .docx | Máx: 10MB
                </p>
              </div>
            ) : (
              <div style={{
                border: '1px solid #BBF7D0',
                background: '#F0FDF4',
                padding: '1rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span style={{ fontSize: '1.5rem' }}>📄</span>
                  <div>
                    <p style={{ fontWeight: 700, fontSize: '0.875rem' }}>{file.name}</p>
                    <p className="meta">{(file.size / 1024).toFixed(1)} KB</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setFile(null)}
                  style={{
                    background: 'none',
                    border: 'none',
                    fontSize: '1.25rem',
                    cursor: 'pointer',
                    color: 'var(--color-subtle)'
                  }}
                >
                  ✕
                </button>
              </div>
            )}
            
            <input
              ref={fileInputRef}
              type="file"
              accept=".md,.txt,.docx"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
          </div>

          {/* Error */}
          {error && (
            <div style={{
              background: '#FEF2F2',
              border: '1px solid #FCA5A5',
              padding: '0.75rem 1rem',
              marginBottom: '1.5rem',
              color: '#B91C1C',
              fontSize: '0.875rem'
            }}>
              ⚠️ {error}
            </div>
          )}

          {/* Info */}
          <div style={{
            background: '#EFF6FF',
            border: '1px solid #BFDBFE',
            padding: '1rem',
            marginBottom: '1.5rem'
          }}>
            <p className="label" style={{ color: '#1E40AF', marginBottom: '0.75rem' }}>
              ℹ️ ¿Qué sucederá?
            </p>
            <ol className="mono" style={{ 
              fontSize: '0.875rem', 
              color: '#1E40AF',
              paddingLeft: '1.25rem',
              lineHeight: 1.8
            }}>
              <li>Analizaremos tu manuscrito con IA (20-40 min)</li>
              <li>Generaremos una "Biblia Narrativa" para tu revisión</li>
              <li>Podrás ajustar el análisis antes de continuar</li>
              <li>El editor IA aplicará cambios editoriales</li>
              <li>Revisarás y aprobarás cada cambio</li>
            </ol>
          </div>

          {/* Buttons */}
          <div style={{ display: 'flex', gap: '1rem' }}>
            <Link to="/" className="btn btn-outline">
              Cancelar
            </Link>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!file || !projectName.trim() || isUploading}
              style={{ 
                flex: 1,
                opacity: (!file || !projectName.trim() || isUploading) ? 0.5 : 1,
                cursor: (!file || !projectName.trim() || isUploading) ? 'not-allowed' : 'pointer'
              }}
            >
              {isUploading ? 'Subiendo...' : 'Crear Proyecto e Iniciar Análisis'}
            </button>
          </div>
        </form>

        {/* Pricing */}
        <div style={{
          marginTop: '2rem',
          padding: '1rem',
          border: '1px solid var(--color-border)',
          background: 'var(--color-surface)',
          textAlign: 'center'
        }}>
          <p className="mono" style={{ fontSize: '0.875rem', color: 'var(--color-subtle)' }}>
            <strong style={{ color: 'var(--color-text)' }}>$49 USD</strong> por libro procesado
          </p>
          <p className="meta" style={{ fontSize: '0.75rem' }}>
            Incluye análisis completo + edición + revisión ilimitada
          </p>
        </div>
      </div>
    </>
  );
}
