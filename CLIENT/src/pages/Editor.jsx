// =============================================================================
// Editor.jsx - VERSIÓN DEFINITIVA (UI MODERNA + LÓGICA PROFESIONAL)
// =============================================================================

import { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { manuscriptAPI } from '../services/api';
import { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType } from 'docx';
import { saveAs } from 'file-saver';
import { 
  FileText, Download, ArrowLeft, Loader2, 
  BookOpen, Check, X, Save, Filter, AlertCircle 
} from 'lucide-react';

export default function Editor() {
  const { id: projectId } = useParams();
  
  // --- ESTADOS ---
  const [chapters, setChapters] = useState([]);
  const [changes, setChanges] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeChapterIdx, setActiveChapterIdx] = useState(0);
  const [filter, setFilter] = useState('all'); // all, pending, accepted, rejected
  const [isExporting, setIsExporting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // --- CARGA DE DATOS ---
  useEffect(() => {
    loadData();
  }, [projectId]);

  async function loadData() {
    try {
      setLoading(true);
      const [summaryData, changesData, chaptersData] = await Promise.all([
        manuscriptAPI.getSummary(projectId).catch(() => null),
        manuscriptAPI.getChanges(projectId).catch(() => ({ changes: [] })),
        manuscriptAPI.getChapters(projectId).catch(() => []), // Si falla, devuelve array vacío
      ]);

      setSummary(summaryData);
      setChanges(changesData.changes || []);

      // --- CORRECCIÓN AQUÍ ---
      // Detectar si chaptersData es un Array directo (lo actual) o un Objeto (lo antiguo)
      let loadedChapters = [];
      if (Array.isArray(chaptersData)) {
          loadedChapters = chaptersData;
      } else if (chaptersData && chaptersData.chapters) {
          loadedChapters = chaptersData.chapters;
      }

      if (loadedChapters.length > 0) {
        setChapters(loadedChapters);
      } else {
        // Fallback: Si no hay capítulos, intentamos armar el esqueleto con los cambios
        const changesArray = changesData.changes || [];
        const uniqueIds = [...new Set(changesArray.map(c => c.chapter_id))].sort((a, b) => a - b);
        setChapters(uniqueIds.map(id => ({
          chapter_id: id,
          display_title: changesArray.find(c => c.chapter_id === id)?.chapter_title || `Capítulo ${id}`,
          contenido_original: '', // No tenemos texto, se queda vacío
          contenido_editado: ''
        })));
      }
    } catch (err) {
      console.error(err);
      setError("No se pudieron cargar los datos del manuscrito.");
    } finally {
      setLoading(false);
    }
  }

  // --- DERIVADOS (MEMOS) ---
  const activeChapter = chapters[activeChapterIdx];
  
  const currentChapterChanges = useMemo(() => {
    if (!activeChapter) return [];
    return changes.filter(c => c.chapter_id === activeChapter.chapter_id);
  }, [changes, activeChapter]);

  const filteredChanges = useMemo(() => {
    if (filter === 'all') return currentChapterChanges;
    return currentChapterChanges.filter(c => c.status === filter);
  }, [currentChapterChanges, filter]);

  const stats = useMemo(() => {
    const total = changes.length;
    const pending = changes.filter(c => c.status === 'pending').length;
    return { total, pending, progress: total > 0 ? Math.round(((total - pending) / total) * 100) : 100 };
  }, [changes]);

  // --- ACCIONES ---
  function updateChangeStatus(changeId, newStatus) {
    setChanges(prev => prev.map(c => 
      c.change_id === changeId 
        ? { ...c, status: newStatus, user_decision: { action: newStatus, timestamp: new Date().toISOString() } }
        : c
    ));
  }

  function bulkUpdateChapter(status) {
    if (!activeChapter) return;
    setChanges(prev => prev.map(c => 
      c.chapter_id === activeChapter.chapter_id && c.status === 'pending'
        ? { ...c, status, user_decision: { action: status, timestamp: new Date().toISOString() } }
        : c
    ));
  }

  async function saveDecisions() {
    try {
      setIsSaving(true);
      const decisions = changes.map(c => ({ change_id: c.change_id, status: c.status }));
      await manuscriptAPI.saveAllDecisions(projectId, decisions);
      alert('✓ Decisiones guardadas en la nube');
    } catch (err) {
      alert('Error al guardar: ' + err.message);
    } finally {
      setIsSaving(false);
    }
  }

  // --- EXPORTACIÓN DOCX (CORREGIDA) ---
  async function exportToDocx() {
    try {
      setIsExporting(true);
      const changesByChapter = {};
      changes.forEach(c => {
        if (!changesByChapter[c.chapter_id]) changesByChapter[c.chapter_id] = [];
        changesByChapter[c.chapter_id].push(c);
      });

      const children = [];

      // Título
      children.push(
        new Paragraph({
          children: [new TextRun({ text: summary?.book_name || 'Manuscrito', bold: true, size: 56, font: 'Georgia' })],
          alignment: AlignmentType.CENTER,
          spacing: { after: 600 }
        })
      );

      for (const chapter of chapters) {
        const chChanges = changesByChapter[chapter.chapter_id] || [];
        
        // Header Capítulo
        children.push(
          new Paragraph({
            children: [new TextRun({ text: chapter.display_title || `Capítulo`, bold: true, size: 36, font: 'Georgia' })],
            heading: HeadingLevel.HEADING_1,
            spacing: { before: 600, after: 400 },
            pageBreakBefore: true
          })
        );

        // LOGICA CORREGIDA: Usar Original como base
        let content = chapter.contenido_original || '';
        if (!content) content = chapter.contenido_editado || ''; // Fallback

        // Aplicar solo cambios ACEPTADOS
        for (const change of chChanges) {
          if (change.status === 'accepted' && change.original && change.editado) {
             // Reemplazo global simple
             content = content.split(change.original).join(change.editado);
          }
        }

        // Generar párrafos
        if (content) {
          const paragraphs = content.split(/\n\n+/);
          for (const para of paragraphs) {
            if (para.trim()) {
              children.push(
                new Paragraph({
                  children: [new TextRun({ text: para.trim(), size: 24, font: 'Times New Roman' })],
                  spacing: { after: 200, line: 360 }
                })
              );
            }
          }
        } else {
           children.push(new Paragraph({ text: "[Capítulo vacío o sin contenido procesado]", italics: true }));
        }
      }

      const doc = new Document({ sections: [{ children }] });
      const blob = await Packer.toBlob(doc);
      saveAs(blob, `${(summary?.book_name || 'Libro').replace(/\s+/g, '_')}_Editado.docx`);

    } catch (err) {
      console.error(err);
      alert('Error exportando: ' + err.message);
    } finally {
      setIsExporting(false);
    }
  }

  // --- RENDER ---
  if (loading) return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-50">
      <Loader2 className="w-10 h-10 animate-spin text-theme-primary mb-4" />
      <p className="text-gray-500 font-mono text-xs uppercase tracking-widest">Cargando Editor...</p>
    </div>
  );

  if (error) return (
    <div className="flex flex-col items-center justify-center h-screen bg-red-50 text-red-700">
      <AlertCircle className="w-12 h-12 mb-4" />
      <h2 className="text-xl font-bold mb-2">Error de Carga</h2>
      <p>{error}</p>
      <Link to="/dashboard" className="mt-6 btn btn-outline bg-white border-red-200">Volver</Link>
    </div>
  );

  return (
    <div className="flex h-screen bg-[#f8f9fa] font-sans overflow-hidden">
      
      {/* SIDEBAR: Índice de Capítulos */}
      <aside className="w-72 bg-white border-r border-gray-200 flex flex-col shrink-0 z-20">
        <div className="p-5 border-b border-gray-100 bg-gray-50/50">
          <h2 className="font-bold text-gray-800 flex items-center gap-2 text-sm uppercase tracking-wide">
            <BookOpen className="w-4 h-4 text-theme-primary" /> Índice
          </h2>
        </div>
        
        <div className="flex-1 overflow-y-auto p-3 space-y-1 custom-scrollbar">
          {chapters.map((chap, idx) => {
             const chChanges = changes.filter(c => c.chapter_id === chap.chapter_id);
             const pending = chChanges.filter(c => c.status === 'pending').length;
             
             return (
              <button
                key={idx}
                onClick={() => setActiveChapterIdx(idx)}
                className={`w-full text-left px-4 py-3 rounded-lg text-sm transition-all group relative
                  ${activeChapterIdx === idx 
                    ? 'bg-gray-900 text-white font-medium shadow-md' 
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'}`}
              >
                <div className="truncate pr-6">{chap.display_title || `Capítulo ${chap.chapter_id}`}</div>
                {pending > 0 && (
                  <span className={`absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-bold px-1.5 py-0.5 rounded-full
                    ${activeChapterIdx === idx ? 'bg-yellow-500 text-black' : 'bg-yellow-100 text-yellow-700'}`}>
                    {pending}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        <div className="p-4 border-t border-gray-100 bg-gray-50/50">
           <Link to="/dashboard" className="text-xs font-bold text-gray-400 hover:text-gray-700 flex items-center gap-2 justify-center transition-colors">
             <ArrowLeft className="w-3 h-3" /> DASHBOARD
           </Link>
        </div>
      </aside>

      {/* ÁREA PRINCIPAL */}
      <div className="flex-1 flex flex-col min-w-0">
        
        {/* HEADER: Herramientas */}
        <header className="h-16 bg-white border-b border-gray-200 flex justify-between items-center px-8 shrink-0 shadow-sm z-10">
           <div className="flex items-center gap-6">
              <h1 className="font-editorial text-xl text-gray-900 truncate max-w-md">
                {activeChapter?.display_title}
              </h1>
              
              <div className="h-6 w-px bg-gray-200"></div>
              
              {/* Filtros */}
              <div className="flex items-center bg-gray-100 rounded-lg p-1">
                 {['all', 'pending', 'accepted', 'rejected'].map(f => (
                   <button
                     key={f}
                     onClick={() => setFilter(f)}
                     className={`px-3 py-1 rounded-md text-xs font-bold capitalize transition-all
                       ${filter === f ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                   >
                     {f === 'all' ? 'Todos' : f}
                   </button>
                 ))}
              </div>
           </div>

           <div className="flex items-center gap-3">
             <div className="flex flex-col items-end mr-4">
                <span className="text-[10px] text-gray-400 font-bold tracking-wider uppercase">Progreso</span>
                <div className="flex items-center gap-2">
                   <div className="w-24 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-green-500 transition-all duration-500" style={{ width: `${stats.progress}%` }}></div>
                   </div>
                   <span className="text-xs font-mono text-gray-600">{stats.progress}%</span>
                </div>
             </div>

             <button 
                onClick={saveDecisions} 
                disabled={isSaving}
                className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 text-gray-700 rounded-md text-xs font-bold uppercase hover:bg-gray-50 transition-all"
             >
                <Save className="w-3 h-3" /> {isSaving ? 'Guardando...' : 'Guardar'}
             </button>

             <button 
                onClick={exportToDocx} 
                disabled={isExporting}
                className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-md text-xs font-bold uppercase hover:bg-black transition-all shadow-md hover:shadow-lg disabled:opacity-50"
             >
               {isExporting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
               Exportar DOCX
             </button>
           </div>
        </header>

        {/* BODY: Lista de Cambios */}
        <div className="flex-1 overflow-y-auto bg-[#f8f9fa] p-8 lg:p-12 custom-scrollbar">
           <div className="max-w-4xl mx-auto space-y-6">
              
              {/* Acciones Rápidas Capítulo */}
              <div className="flex justify-between items-center mb-6">
                 <span className="text-sm font-bold text-gray-400 uppercase tracking-widest">
                   {filteredChanges.length} cambios {filter !== 'all' && `(${filter})`}
                 </span>
                 <div className="flex gap-2">
                    <button onClick={() => bulkUpdateChapter('accepted')} className="text-xs font-bold text-green-700 hover:bg-green-50 px-3 py-1.5 rounded transition-colors">
                       ✓ Aceptar Todo en Capítulo
                    </button>
                    <button onClick={() => bulkUpdateChapter('rejected')} className="text-xs font-bold text-red-700 hover:bg-red-50 px-3 py-1.5 rounded transition-colors">
                       ✕ Rechazar Todo en Capítulo
                    </button>
                 </div>
              </div>

              {filteredChanges.length === 0 ? (
                 <div className="flex flex-col items-center justify-center h-64 border-2 border-dashed border-gray-200 rounded-xl text-gray-400">
                    <Filter className="w-8 h-8 mb-2 opacity-50" />
                    <p>No hay cambios que coincidan con el filtro</p>
                 </div>
              ) : (
                 filteredChanges.map(change => (
                    <ChangeCard 
                       key={change.change_id} 
                       change={change} 
                       onAccept={() => updateChangeStatus(change.change_id, 'accepted')}
                       onReject={() => updateChangeStatus(change.change_id, 'rejected')}
                       onReset={() => updateChangeStatus(change.change_id, 'pending')}
                    />
                 ))
              )}
           </div>
        </div>
      </div>
    </div>
  );
}

// --- SUBCOMPONENTE: Tarjeta de Cambio (Estilizada) ---
function ChangeCard({ change, onAccept, onReject, onReset }) {
  const statusStyles = {
    pending: { border: 'border-yellow-200', bg: 'bg-white', badge: 'bg-yellow-100 text-yellow-800' },
    accepted: { border: 'border-green-200', bg: 'bg-green-50/30', badge: 'bg-green-100 text-green-800' },
    rejected: { border: 'border-red-200', bg: 'bg-red-50/30', badge: 'bg-red-100 text-red-800' }
  };

  const currentStyle = statusStyles[change.status] || statusStyles.pending;

  return (
    <div className={`rounded-xl border ${currentStyle.border} ${currentStyle.bg} shadow-sm transition-all hover:shadow-md`}>
       {/* Header Tarjeta */}
       <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
          <div className="flex items-center gap-3">
             <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-md ${currentStyle.badge}`}>
                {change.status === 'pending' ? 'Pendiente' : change.status === 'accepted' ? 'Aceptado' : 'Rechazado'}
             </span>
             <span className="text-xs font-bold text-indigo-600 bg-indigo-50 px-2 py-1 rounded-md uppercase">
                {change.tipo || 'Mejora'}
             </span>
          </div>
          <span className="text-xs text-gray-400 italic">
             {change.impacto_narrativo ? `Impacto: ${change.impacto_narrativo}` : 'Ajuste estilístico'}
          </span>
       </div>

       {/* Contenido */}
       <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Original */}
          <div className="space-y-2">
             <span className="text-[10px] font-bold text-red-400 uppercase tracking-widest block mb-1">Original</span>
             <div className={`p-4 rounded-lg bg-red-50 text-gray-700 text-sm leading-relaxed font-serif ${change.status === 'accepted' ? 'line-through opacity-50' : ''}`}>
                {change.original}
             </div>
          </div>
          
          {/* Editado */}
          <div className="space-y-2">
             <span className="text-[10px] font-bold text-green-500 uppercase tracking-widest block mb-1">Propuesta IA</span>
             <div className={`p-4 rounded-lg bg-green-50 text-gray-800 text-sm leading-relaxed font-serif ${change.status === 'rejected' ? 'opacity-50' : ''}`}>
                {change.editado}
             </div>
          </div>
       </div>

       {/* Footer: Justificación y Botones */}
       <div className="px-6 py-4 bg-gray-50/50 border-t border-gray-100 rounded-b-xl flex justify-between items-center">
          <p className="text-xs text-gray-500 max-w-lg">
             <span className="font-bold text-gray-700">Motivo:</span> {change.justificacion || 'Mejora de fluidez y claridad.'}
          </p>

          <div className="flex gap-2">
             {change.status !== 'pending' && (
                <button onClick={onReset} className="text-xs font-bold text-gray-400 hover:text-gray-600 px-3 py-1.5 transition-colors">
                   Deshacer
                </button>
             )}
             
             {change.status !== 'rejected' && (
                <button onClick={onReject} className="flex items-center gap-1.5 text-xs font-bold text-red-600 bg-white border border-red-100 hover:bg-red-50 px-3 py-1.5 rounded-lg shadow-sm transition-all">
                   <X className="w-3 h-3" /> Rechazar
                </button>
             )}
             
             {change.status !== 'accepted' && (
                <button onClick={onAccept} className="flex items-center gap-1.5 text-xs font-bold text-green-700 bg-green-100 hover:bg-green-200 border border-green-200 px-4 py-1.5 rounded-lg shadow-sm transition-all">
                   <Check className="w-3 h-3" /> Aceptar
                </button>
             )}
          </div>
       </div>
    </div>
  );
}