// =============================================================================
// Editor.jsx - EDITOR CON TRACK CHANGES Y EXPORT DOCX PROFESIONAL
// =============================================================================

import { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { manuscriptAPI } from '../services/api';
import { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType } from 'docx';
import { saveAs } from 'file-saver';

export default function Editor() {
  const { id: projectId } = useParams();
  
  // Estados
  const [chapters, setChapters] = useState([]);
  const [changes, setChanges] = useState([]);
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentChapterIndex, setCurrentChapterIndex] = useState(0);
  const [filter, setFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [isExporting, setIsExporting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Cargar datos
  useEffect(() => {
    loadData();
  }, [projectId]);

  async function loadData() {
    try {
      setIsLoading(true);
      
      const [summaryData, changesData, chaptersData] = await Promise.all([
        manuscriptAPI.getSummary(projectId).catch(() => null),
        manuscriptAPI.getChanges(projectId).catch(() => ({ changes: [] })),
        manuscriptAPI.getChapters(projectId).catch(() => ({ chapters: [] })),
      ]);
      
      setSummary(summaryData);
      setChanges(changesData.changes || []);
      
      // Usar capítulos del backend si existen, sino extraer de cambios
      if (chaptersData.chapters && chaptersData.chapters.length > 0) {
        setChapters(chaptersData.chapters);
      } else {
        const changesArray = changesData.changes || [];
        const uniqueChapters = [...new Set(changesArray.map(c => c.chapter_id))].sort((a, b) => a - b);
        setChapters(uniqueChapters.map(id => ({
          chapter_id: id,
          display_title: changesArray.find(c => c.chapter_id === id)?.chapter_title || `Capítulo ${id}`,
          contenido_editado: ''
        })));
      }
      
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  // Cambios del capítulo actual
  const currentChapterChanges = useMemo(() => {
    if (chapters.length === 0) return [];
    const currentChapterId = chapters[currentChapterIndex]?.chapter_id;
    return changes.filter(c => c.chapter_id === currentChapterId);
  }, [changes, chapters, currentChapterIndex]);

  // Cambios filtrados
  const filteredChanges = useMemo(() => {
    let result = currentChapterChanges;
    if (filter !== 'all') result = result.filter(c => c.status === filter);
    if (typeFilter !== 'all') result = result.filter(c => c.tipo === typeFilter);
    return result;
  }, [currentChapterChanges, filter, typeFilter]);

  // Tipos únicos
  const changeTypes = useMemo(() => {
    return [...new Set(changes.map(c => c.tipo))];
  }, [changes]);

  // Estadísticas
  const stats = useMemo(() => {
    const pending = changes.filter(c => c.status === 'pending').length;
    const accepted = changes.filter(c => c.status === 'accepted').length;
    const rejected = changes.filter(c => c.status === 'rejected').length;
    return { total: changes.length, pending, accepted, rejected };
  }, [changes]);

  // Actualizar estado de un cambio
  function updateChangeStatus(changeId, newStatus) {
    setChanges(prev => prev.map(c => 
      c.change_id === changeId 
        ? { ...c, status: newStatus, user_decision: { action: newStatus, timestamp: new Date().toISOString() } }
        : c
    ));
  }

  // Bulk updates
  function bulkUpdateChapter(status) {
    const currentChapterId = chapters[currentChapterIndex]?.chapter_id;
    setChanges(prev => prev.map(c => 
      c.chapter_id === currentChapterId && c.status === 'pending'
        ? { ...c, status, user_decision: { action: status, timestamp: new Date().toISOString() } }
        : c
    ));
  }

  function bulkUpdateAll(status) {
    setChanges(prev => prev.map(c => 
      c.status === 'pending'
        ? { ...c, status, user_decision: { action: status, timestamp: new Date().toISOString() } }
        : c
    ));
  }

  // Guardar decisiones en backend
  async function saveDecisions() {
    try {
      setIsSaving(true);
      const decisions = changes.map(c => ({
        change_id: c.change_id,
        status: c.status
      }));
      await manuscriptAPI.saveAllDecisions(projectId, decisions);
      alert('✓ Decisiones guardadas');
    } catch (err) {
      alert('Error al guardar: ' + err.message);
    } finally {
      setIsSaving(false);
    }
  }

  // EXPORT A DOCX - VERSIÓN PROFESIONAL
  async function exportToDocx() {
    try {
      setIsExporting(true);
      
      // Agrupar cambios por capítulo
      const changesByChapter = {};
      changes.forEach(c => {
        if (!changesByChapter[c.chapter_id]) changesByChapter[c.chapter_id] = [];
        changesByChapter[c.chapter_id].push(c);
      });
      
      const children = [];
      
      // Título del libro
      children.push(
        new Paragraph({
          children: [
            new TextRun({ 
              text: summary?.book_name || 'Manuscrito Editado', 
              bold: true, 
              size: 56,
              font: 'Georgia'
            })
          ],
          alignment: AlignmentType.CENTER,
          spacing: { after: 600 }
        })
      );
      
      // Subtítulo
      children.push(
        new Paragraph({
          children: [
            new TextRun({ 
              text: 'Editado con Sylphrena', 
              italics: true,
              size: 24,
              color: '666666'
            })
          ],
          alignment: AlignmentType.CENTER,
          spacing: { after: 800 }
        })
      );
      
      // Separador
      children.push(new Paragraph({ text: '', spacing: { after: 400 } }));
      
      // Procesar cada capítulo
      for (const chapter of chapters) {
        const chapterId = chapter.chapter_id;
        const chapterChanges = changesByChapter[chapterId] || [];
        
        // Título del capítulo
        children.push(
          new Paragraph({
            children: [
              new TextRun({ 
                text: chapter.display_title || `Capítulo ${chapterId}`, 
                bold: true, 
                size: 36,
                font: 'Georgia'
              })
            ],
            heading: HeadingLevel.HEADING_1,
            spacing: { before: 600, after: 400 },
            pageBreakBefore: chapterId > 1
          })
        );
        
        // Obtener contenido editado del capítulo
        let content = chapter.contenido_editado || chapter.contenido_original || '';
        
        // Aplicar cambios aceptados al contenido
        for (const change of chapterChanges) {
          if (change.status === 'accepted' && change.original && change.editado) {
            // Reemplazar el texto original con el editado
            content = content.replace(change.original, change.editado);
          }
          // Si está rechazado, mantener el original (no hacer nada)
        }
        
        // Si no hay contenido, mostrar los cambios como párrafos
        if (!content && chapterChanges.length > 0) {
          for (const change of chapterChanges) {
            const text = change.status === 'accepted' ? change.editado : change.original;
            children.push(
              new Paragraph({
                children: [new TextRun({ text, size: 24 })],
                spacing: { after: 200 }
              })
            );
          }
        } else if (content) {
          // Dividir contenido en párrafos
          const paragraphs = content.split(/\n\n+/);
          for (const para of paragraphs) {
            if (para.trim()) {
              children.push(
                new Paragraph({
                  children: [new TextRun({ text: para.trim(), size: 24 })],
                  spacing: { after: 200, line: 360 }
                })
              );
            }
          }
        }
      }
      
      // Crear documento
      const doc = new Document({
        creator: 'Sylphrena',
        title: summary?.book_name || 'Manuscrito Editado',
        description: 'Manuscrito editado con Sylphrena AI',
        sections: [{
          properties: {
            page: {
              margin: {
                top: 1440,    // 1 inch
                right: 1440,
                bottom: 1440,
                left: 1440
              }
            }
          },
          children
        }]
      });
      
      const blob = await Packer.toBlob(doc);
      const filename = `${(summary?.book_name || 'manuscrito').replace(/[^a-zA-Z0-9]/g, '_')}_editado.docx`;
      saveAs(blob, filename);
      
    } catch (err) {
      console.error('Export error:', err);
      alert('Error al exportar: ' + err.message);
    } finally {
      setIsExporting(false);
    }
  }

  // Loading
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

  // Error
  if (error) {
    return (
      <div className="content-section" style={{ borderColor: '#FCA5A5', background: '#FEF2F2' }}>
        <h2 className="title-section" style={{ color: '#B91C1C' }}>Error al Cargar</h2>
        <p style={{ color: '#B91C1C' }}>{error}</p>
        <Link to="/" className="btn btn-outline" style={{ marginTop: '1rem' }}>← Volver</Link>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)' }}>
      {/* HEADER */}
      <header className="page-header" style={{ flexShrink: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <Link to="/" className="meta" style={{ display: 'block', marginBottom: '0.5rem' }}>
              ← Volver al Dashboard
            </Link>
            <h1 className="title-main">EDITOR DE CAMBIOS</h1>
            <p className="page-header-meta">
              {summary?.book_name} | {stats.total} cambios ({stats.pending} pendientes)
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button 
              className="btn btn-outline"
              onClick={saveDecisions}
              disabled={isSaving}
            >
              {isSaving ? 'Guardando...' : '💾 Guardar'}
            </button>
            <button 
              className="btn btn-primary"
              onClick={exportToDocx}
              disabled={isExporting || stats.pending > 0}
              title={stats.pending > 0 ? 'Resuelve todos los cambios primero' : ''}
            >
              {isExporting ? 'Exportando...' : '📄 Exportar DOCX'}
            </button>
          </div>
        </div>
      </header>

      {/* STATS BAR */}
      <div style={{ 
        display: 'flex', 
        gap: '1rem', 
        padding: '0.75rem 1rem',
        background: '#F9FAFB',
        borderBottom: '1px solid var(--color-border)',
        flexShrink: 0
      }}>
        <StatBadge label="Total" value={stats.total} color="#6B7280" />
        <StatBadge label="Pendientes" value={stats.pending} color="#F59E0B" />
        <StatBadge label="Aceptados" value={stats.accepted} color="#10B981" />
        <StatBadge label="Rechazados" value={stats.rejected} color="#EF4444" />
        
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem' }}>
          <button 
            className="btn"
            style={{ background: '#D1FAE5', color: '#065F46', fontSize: '0.8rem' }}
            onClick={() => bulkUpdateAll('accepted')}
            disabled={stats.pending === 0}
          >
            ✓ Aceptar Todo
          </button>
          <button 
            className="btn"
            style={{ background: '#FEE2E2', color: '#B91C1C', fontSize: '0.8rem' }}
            onClick={() => bulkUpdateAll('rejected')}
            disabled={stats.pending === 0}
          >
            ✕ Rechazar Todo
          </button>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        
        {/* SIDEBAR */}
        <aside style={{ 
          width: '220px', 
          borderRight: '1px solid var(--color-border)',
          overflowY: 'auto',
          flexShrink: 0
        }}>
          <div style={{ padding: '0.75rem', borderBottom: '1px solid var(--color-border)' }}>
            <span className="label">CAPÍTULOS</span>
          </div>
          {chapters.map((chapter, idx) => {
            const chapterId = chapter.chapter_id;
            const chapterChanges = changes.filter(c => c.chapter_id === chapterId);
            const pending = chapterChanges.filter(c => c.status === 'pending').length;
            
            return (
              <button
                key={chapterId}
                onClick={() => setCurrentChapterIndex(idx)}
                style={{
                  display: 'block',
                  width: '100%',
                  padding: '0.75rem',
                  textAlign: 'left',
                  border: 'none',
                  borderBottom: '1px solid var(--color-border)',
                  background: idx === currentChapterIndex ? '#E5E7EB' : 'transparent',
                  cursor: 'pointer',
                  fontSize: '0.875rem'
                }}
              >
                <div style={{ fontWeight: idx === currentChapterIndex ? 700 : 400 }}>
                  {chapter.display_title || `Capítulo ${chapterId}`}
                </div>
                <div className="meta" style={{ marginTop: '0.25rem' }}>
                  {chapterChanges.length} cambios
                  {pending > 0 && (
                    <span style={{ color: '#F59E0B', marginLeft: '0.5rem' }}>
                      ({pending} pendientes)
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </aside>

        {/* MAIN */}
        <main style={{ flex: 1, overflowY: 'auto', padding: '1rem' }}>
          
          {/* Filtros */}
          <div style={{ 
            display: 'flex', 
            gap: '0.5rem', 
            marginBottom: '1rem',
            flexWrap: 'wrap',
            alignItems: 'center'
          }}>
            <span className="label" style={{ marginRight: '0.5rem' }}>Filtrar:</span>
            
            {['all', 'pending', 'accepted', 'rejected'].map(f => (
              <FilterButton 
                key={f}
                active={filter === f} 
                onClick={() => setFilter(f)}
                color={f === 'pending' ? '#F59E0B' : f === 'accepted' ? '#10B981' : f === 'rejected' ? '#EF4444' : '#6B7280'}
              >
                {f === 'all' ? 'Todos' : f === 'pending' ? 'Pendientes' : f === 'accepted' ? 'Aceptados' : 'Rechazados'}
              </FilterButton>
            ))}
            
            <span style={{ margin: '0 0.5rem', color: '#D1D5DB' }}>|</span>
            
            <select 
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem', border: '1px solid var(--color-border)' }}
            >
              <option value="all">Todos los tipos</option>
              {changeTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          {/* Acciones capítulo */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1rem',
            padding: '0.5rem',
            background: '#F9FAFB',
            borderRadius: '4px'
          }}>
            <span className="mono" style={{ fontSize: '0.875rem' }}>
              {chapters[currentChapterIndex]?.display_title} - {filteredChanges.length} cambios
            </span>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button 
                className="btn btn-outline"
                style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                onClick={() => bulkUpdateChapter('accepted')}
              >
                ✓ Aceptar capítulo
              </button>
              <button 
                className="btn btn-outline"
                style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                onClick={() => bulkUpdateChapter('rejected')}
              >
                ✕ Rechazar capítulo
              </button>
            </div>
          </div>

          {/* Lista de cambios */}
          {filteredChanges.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#6B7280' }}>
              No hay cambios que mostrar
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {filteredChanges.map(change => (
                <ChangeCard 
                  key={change.change_id}
                  change={change}
                  onAccept={() => updateChangeStatus(change.change_id, 'accepted')}
                  onReject={() => updateChangeStatus(change.change_id, 'rejected')}
                  onReset={() => updateChangeStatus(change.change_id, 'pending')}
                />
              ))}
            </div>
          )}
        </main>
      </div>

      {/* Progress bar */}
      <div style={{ 
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        background: 'var(--color-surface)',
        borderTop: '1px solid var(--color-border)',
        padding: '0.75rem 1rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span className="mono" style={{ fontSize: '0.875rem' }}>
            Progreso: {stats.accepted + stats.rejected} / {stats.total}
          </span>
          <div style={{ 
            flex: 1, 
            height: '8px', 
            background: '#E5E7EB',
            borderRadius: '4px',
            overflow: 'hidden',
            display: 'flex'
          }}>
            <div style={{ 
              height: '100%',
              width: `${(stats.accepted / stats.total) * 100}%`,
              background: '#10B981',
              transition: 'width 0.3s ease'
            }} />
            <div style={{ 
              height: '100%',
              width: `${(stats.rejected / stats.total) * 100}%`,
              background: '#EF4444',
              transition: 'width 0.3s ease'
            }} />
          </div>
          <span className="mono" style={{ fontSize: '0.75rem', color: '#6B7280' }}>
            {Math.round(((stats.accepted + stats.rejected) / stats.total) * 100)}%
          </span>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// COMPONENTES AUXILIARES
// =============================================================================

function StatBadge({ label, value, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
      <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: color }} />
      <span className="mono" style={{ fontSize: '0.8rem' }}>
        {label}: <strong>{value}</strong>
      </span>
    </div>
  );
}

function FilterButton({ active, onClick, children, color = '#6B7280' }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '0.25rem 0.75rem',
        fontSize: '0.8rem',
        border: active ? 'none' : '1px solid var(--color-border)',
        background: active ? color : 'transparent',
        color: active ? 'white' : 'inherit',
        borderRadius: '4px',
        cursor: 'pointer'
      }}
    >
      {children}
    </button>
  );
}

function ChangeCard({ change, onAccept, onReject, onReset }) {
  const statusColors = {
    pending: { bg: '#FEF3C7', border: '#F59E0B', text: '#92400E' },
    accepted: { bg: '#D1FAE5', border: '#10B981', text: '#065F46' },
    rejected: { bg: '#FEE2E2', border: '#EF4444', text: '#B91C1C' }
  };
  
  const colors = statusColors[change.status] || statusColors.pending;
  
  const typeColors = {
    redundancia: '#8B5CF6',
    claridad: '#3B82F6',
    fluidez: '#10B981',
    estilo: '#F59E0B',
    'show-tell': '#EC4899',
    gramatica: '#6366F1',
    puntuacion: '#14B8A6',
    otro: '#6B7280'
  };
  
  return (
    <div style={{ 
      border: `1px solid ${colors.border}`,
      background: colors.bg,
      borderRadius: '8px',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '0.5rem 1rem',
        borderBottom: `1px solid ${colors.border}`,
        background: 'rgba(255,255,255,0.5)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span 
            style={{ 
              background: typeColors[change.tipo?.toLowerCase()] || typeColors.otro,
              color: 'white',
              padding: '0.125rem 0.5rem',
              borderRadius: '4px',
              fontSize: '0.7rem',
              fontWeight: 600
            }}
          >
            {change.tipo?.toUpperCase()}
          </span>
          {change.impacto_narrativo && (
            <span className="meta">Impacto: {change.impacto_narrativo}</span>
          )}
        </div>
        <span style={{ fontSize: '0.75rem', color: colors.text, fontWeight: 600 }}>
          {change.status === 'pending' ? '⏳ Pendiente' : 
           change.status === 'accepted' ? '✓ Aceptado' : '✕ Rechazado'}
        </span>
      </div>
      
      {/* Content */}
      <div style={{ padding: '1rem' }}>
        {/* Original */}
        <div style={{ marginBottom: '1rem' }}>
          <span className="label" style={{ color: '#B91C1C', display: 'block', marginBottom: '0.25rem' }}>
            ORIGINAL
          </span>
          <div style={{ 
            background: '#FEE2E2',
            padding: '0.75rem',
            borderRadius: '4px',
            fontSize: '0.9rem',
            lineHeight: 1.6,
            textDecoration: change.status === 'accepted' ? 'line-through' : 'none',
            opacity: change.status === 'accepted' ? 0.6 : 1
          }}>
            {change.original}
          </div>
        </div>
        
        {/* Editado */}
        <div style={{ marginBottom: '1rem' }}>
          <span className="label" style={{ color: '#059669', display: 'block', marginBottom: '0.25rem' }}>
            PROPUESTA
          </span>
          <div style={{ 
            background: '#D1FAE5',
            padding: '0.75rem',
            borderRadius: '4px',
            fontSize: '0.9rem',
            lineHeight: 1.6,
            opacity: change.status === 'rejected' ? 0.6 : 1
          }}>
            {change.editado}
          </div>
        </div>
        
        {/* Justificación */}
        {change.justificacion && (
          <div style={{ 
            background: '#F3F4F6',
            padding: '0.75rem',
            borderRadius: '4px',
            fontSize: '0.85rem',
            color: '#4B5563',
            marginBottom: '1rem'
          }}>
            <strong>Justificación:</strong> {change.justificacion}
          </div>
        )}
        
        {/* Actions */}
        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
          {change.status !== 'pending' && (
            <button className="btn btn-outline" onClick={onReset} style={{ fontSize: '0.8rem' }}>
              ↩ Deshacer
            </button>
          )}
          {change.status !== 'rejected' && (
            <button 
              className="btn"
              onClick={onReject}
              style={{ background: '#FEE2E2', color: '#B91C1C', fontSize: '0.8rem' }}
            >
              ✕ Rechazar
            </button>
          )}
          {change.status !== 'accepted' && (
            <button 
              className="btn"
              onClick={onAccept}
              style={{ background: '#D1FAE5', color: '#065F46', fontSize: '0.8rem' }}
            >
              ✓ Aceptar
            </button>
          )}
        </div>
      </div>
    </div>
  );
}