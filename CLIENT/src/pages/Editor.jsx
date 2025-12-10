// =============================================================================
// Editor.jsx - VERSIÓN DEFINITIVA SYLPHRENA 5.0 (Texto + Notas)
// =============================================================================

import { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { manuscriptAPI, editorialAPI } from '../services/api';
import { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType } from 'docx';
import { saveAs } from 'file-saver';
import { 
  FileText, Download, ArrowLeft, Loader2, 
  BookOpen, Check, X, Save, Filter, AlertCircle,
  MessageSquare, PenLine
} from 'lucide-react';

export default function Editor() {
  const { id: projectId } = useParams();
  
  // --- ESTADOS ---
  const [chapters, setChapters] = useState([]);
  const [changes, setChanges] = useState([]);
  const [marginNotes, setMarginNotes] = useState({}); // Nuevo: Mapa de notas por capítulo
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeChapterIdx, setActiveChapterIdx] = useState(0);
  const [filter, setFilter] = useState('all'); // all, pending, accepted, rejected
  const [isExporting, setIsExporting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [editorMode, setEditorMode] = useState('changes'); // 'changes' | 'notes'

  // --- CARGA DE DATOS ---
  useEffect(() => {
    loadData();
  }, [projectId]);

  async function loadData() {
    try {
      setLoading(true);
      const [summaryData, changesData, chaptersData, notesData] = await Promise.all([
        manuscriptAPI.getSummary(projectId).catch(() => null),
        manuscriptAPI.getChanges(projectId).catch(() => ({ changes: [] })),
        manuscriptAPI.getChapters(projectId).catch(() => []),
        editorialAPI.getMarginNotes(projectId).catch(() => ({ results: [] })) // Nuevo endpoint
      ]);

      setSummary(summaryData);
      setChanges(changesData.changes || []);

      // Procesar capítulos
      let loadedChapters = [];
      if (Array.isArray(chaptersData)) {
          loadedChapters = chaptersData;
      } else if (chaptersData && chaptersData.chapters) {
          loadedChapters = chaptersData.chapters;
      }

      if (loadedChapters.length > 0) {
        setChapters(loadedChapters);
      } else {
        // Fallback si no hay capítulos estructurados
        const changesArray = changesData.changes || [];
        const uniqueIds = [...new Set(changesArray.map(c => c.chapter_id))].sort((a, b) => a - b);
        setChapters(uniqueIds.map(id => ({
          chapter_id: id,
          display_title: changesArray.find(c => c.chapter_id === id)?.chapter_title || `Capítulo ${id}`,
          contenido_original: '',
          contenido_editado: ''
        })));
      }

      // Procesar Notas de Margen (Mapear por ID de capítulo)
      const notesMap = {};
      if (notesData && notesData.results) {
        notesData.results.forEach(res => {
          // Normalizar ID (puede venir como chapter_id string o int)
          const id = res.chapter_id || res.fragment_id;
          if (id) notesMap[String(id)] = res.notas_margen || [];
        });
      }
      setMarginNotes(notesMap);

    } catch (err) {
      console.error(err);
      setError("No se pudieron cargar los datos del manuscrito. Verifica que el proceso haya terminado.");
    } finally {
      setLoading(false);
    }
  }

  // --- DERIVADOS (MEMOS) ---
  const activeChapter = chapters[activeChapterIdx];
  const activeChapterIdStr = activeChapter ? String(activeChapter.chapter_id) : null;
  
  // Cambios de texto para este capítulo
  const currentChapterChanges = useMemo(() => {
    if (!activeChapter) return [];
    return changes.filter(c => String(c.chapter_id) === activeChapterIdStr);
  }, [changes, activeChapterIdStr]);

  // Notas de margen para este capítulo
  const currentChapterNotes = useMemo(() => {
    if (!activeChapterIdStr) return [];
    return marginNotes[activeChapterIdStr] || [];
  }, [marginNotes, activeChapterIdStr]);

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
      String(c.chapter_id) === activeChapterIdStr && c.status === 'pending'
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

  // --- EXPORTACIÓN DOCX ---
  async function exportToDocx() {
    try {
      setIsExporting(true);
      const changesByChapter = {};
      changes.forEach(c => {
        const cid = String(c.chapter_id);
        if (!changesByChapter[cid]) changesByChapter[cid] = [];
        changesByChapter[cid].push(c);
      });

      const children = [];

      // Título Principal
      children.push(
        new Paragraph({
          children: [new TextRun({ text: summary?.book_name || 'Manuscrito', bold: true, size: 56, font: 'Georgia' })],
          alignment: AlignmentType.CENTER,
          spacing: { after: 600 }
        })
      );

      for (const chapter of chapters) {
        const cid = String(chapter.chapter_id);
        const chChanges = changesByChapter[cid] || [];
        
        // Título de Capítulo
        children.push(
          new Paragraph({
            children: [new TextRun({ text: chapter.display_title || `Capítulo`, bold: true, size: 36, font: 'Georgia' })],
            heading: HeadingLevel.HEADING_1,
            spacing: { before: 600, after: 400 },
            pageBreakBefore: true
          })
        );

        // Contenido base
        let content = chapter.contenido_original || '';
        if (!content) content = chapter.contenido_editado || ''; 

        // Aplicar cambios aceptados
        for (const change of chChanges) {
          if (change.status === 'accepted' && change.original && change.editado) {
             content = content.split(change.original).join(change.editado);
          }
        }

        // Renderizar párrafos
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
      <Link to="/dashboard" className="mt-6 btn btn-outline bg-white border-red-200 px-4 py-2 rounded">Volver</Link>
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
             const cid = String(chap.chapter_id);
             const chChanges = changes.filter(c => String(c.chapter_id) === cid);
             const pending = chChanges.filter(c => c.status === 'pending').length;
             const notesCount = marginNotes[cid]?.length || 0;
             
             return (
              <button
                key={idx}
                onClick={() => setActiveChapterIdx(idx)}
                className={`w-full text-left px-4 py-3 rounded-lg text-sm transition-all group relative
                  ${activeChapterIdx === idx 
                    ? 'bg-gray-900 text-white font-medium shadow-md' 
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'}`}
              >
                <div className="truncate pr-8">{chap.display_title || `Capítulo ${chap.chapter_id}`}</div>
                
                {/* Badges de estado */}
                <div className="absolute right-3 top-1/2 -translate-y-1/2 flex gap-1">
                  {pending > 0 && (
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full flex items-center justify-center min-w-[18px]
                      ${activeChapterIdx === idx ? 'bg-yellow-500 text-black' : 'bg-yellow-100 text-yellow-700'}`}>
                      {pending}
                    </span>
                  )}
                  {notesCount > 0 && (
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full flex items-center justify-center min-w-[18px]
                      ${activeChapterIdx === idx ? 'bg-blue-600 text-white' : 'bg-blue-100 text-blue-700'}`}>
                      {notesCount}
                    </span>
                  )}
                </div>
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
        
        {/* HEADER: Herramientas y Tabs */}
        <header className="h-16 bg-white border-b border-gray-200 flex justify-between items-center px-8 shrink-0 shadow-sm z-10">
           <div className="flex items-center gap-6">
              <h1 className="font-editorial text-xl text-gray-900 truncate max-w-[200px] lg:max-w-md">
                {activeChapter?.display_title}
              </h1>
              
              <div className="h-6 w-px bg-gray-200"></div>
              
              {/* TABS DE MODO (NUEVO) */}
              <div className="flex bg-gray-100 p-1 rounded-lg">
                <button
                  onClick={() => setEditorMode('changes')}
                  className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-xs font-bold transition-all ${editorMode === 'changes' ? 'bg-white shadow text-theme-primary' : 'text-gray-500 hover:text-gray-700'}`}
                >
                  <PenLine className="w-3 h-3" /> Edición ({filteredChanges.length})
                </button>
                <button
                  onClick={() => setEditorMode('notes')}
                  className={`flex items-center gap-2 px-4 py-1.5 rounded-md text-xs font-bold transition-all ${editorMode === 'notes' ? 'bg-white shadow text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                >
                  <MessageSquare className="w-3 h-3" /> Notas ({currentChapterNotes.length})
                </button>
              </div>
           </div>

           <div className="flex items-center gap-3">
             <button 
                onClick={saveDecisions} 
                disabled={isSaving}
                className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 text-gray-700 rounded-md text-xs font-bold uppercase hover:bg-gray-50 transition-all"
             >
                <Save className="w-3 h-3" /> {isSaving ? '...' : 'Guardar'}
             </button>

             <button 
                onClick={exportToDocx} 
                disabled={isExporting}
                className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-md text-xs font-bold uppercase hover:bg-black transition-all shadow-md hover:shadow-lg disabled:opacity-50"
             >
               {isExporting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
               Exportar
             </button>
           </div>
        </header>

        {/* BODY: Contenido Dinámico */}
        <div className="flex-1 overflow-y-auto bg-[#f8f9fa] p-8 lg:p-12 custom-scrollbar">
           <div className="max-w-4xl mx-auto space-y-6">
              
              {editorMode === 'changes' ? (
                 /* MODO EDICIÓN DE TEXTO */
                 <>
                    {/* Filtros y Acciones */}
                    <div className="flex justify-between items-center mb-6">
                       <div className="flex items-center bg-gray-200 rounded-lg p-0.5">
                          {['all', 'pending', 'accepted', 'rejected'].map(f => (
                            <button
                              key={f}
                              onClick={() => setFilter(f)}
                              className={`px-3 py-1 rounded-md text-[10px] font-bold uppercase transition-all
                                ${filter === f ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                            >
                              {f === 'all' ? 'Todos' : f}
                            </button>
                          ))}
                       </div>
                       <div className="flex gap-2">
                          <button onClick={() => bulkUpdateChapter('accepted')} className="text-xs font-bold text-green-700 hover:bg-green-50 px-3 py-1.5 rounded transition-colors">
                             ✓ Aceptar Todo
                          </button>
                          <button onClick={() => bulkUpdateChapter('rejected')} className="text-xs font-bold text-red-700 hover:bg-red-50 px-3 py-1.5 rounded transition-colors">
                             ✕ Rechazar Todo
                          </button>
                       </div>
                    </div>

                    {filteredChanges.length === 0 ? (
                       <div className="flex flex-col items-center justify-center h-64 border-2 border-dashed border-gray-200 rounded-xl text-gray-400">
                          <Filter className="w-8 h-8 mb-2 opacity-50" />
                          <p>No hay cambios en esta categoría</p>
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
                 </>
              ) : (
                 /* MODO NOTAS DE MARGEN */
                 <div className="space-y-6 animate-fadeIn">
                    {currentChapterNotes.length === 0 ? (
                      <div className="text-center py-20 text-gray-400 border-2 border-dashed border-gray-200 rounded-xl">
                        <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-20" />
                        <p>No hay notas editoriales para este capítulo.</p>
                      </div>
                    ) : (
                      currentChapterNotes.map((nota, idx) => (
                        <NoteCard key={idx} note={nota} />
                      ))
                    )}
                 </div>
              )}
           </div>
        </div>
      </div>
    </div>
  );
}

// --- SUBCOMPONENTES ---

function ChangeCard({ change, onAccept, onReject, onReset }) {
  const statusStyles = {
    pending: { border: 'border-yellow-200', bg: 'bg-white', badge: 'bg-yellow-100 text-yellow-800' },
    accepted: { border: 'border-green-200', bg: 'bg-green-50/30', badge: 'bg-green-100 text-green-800' },
    rejected: { border: 'border-red-200', bg: 'bg-red-50/30', badge: 'bg-red-100 text-red-800' }
  };

  const currentStyle = statusStyles[change.status] || statusStyles.pending;

  return (
    <div className={`rounded-xl border ${currentStyle.border} ${currentStyle.bg} shadow-sm transition-all hover:shadow-md`}>
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

       <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
             <span className="text-[10px] font-bold text-red-400 uppercase tracking-widest block mb-1">Original</span>
             <div className={`p-4 rounded-lg bg-red-50 text-gray-700 text-sm leading-relaxed font-serif ${change.status === 'accepted' ? 'line-through opacity-50' : ''}`}>
                {change.original}
             </div>
          </div>
          <div className="space-y-2">
             <span className="text-[10px] font-bold text-green-500 uppercase tracking-widest block mb-1">Propuesta IA</span>
             <div className={`p-4 rounded-lg bg-green-50 text-gray-800 text-sm leading-relaxed font-serif ${change.status === 'rejected' ? 'opacity-50' : ''}`}>
                {change.editado}
             </div>
          </div>
       </div>

       <div className="px-6 py-4 bg-gray-50/50 border-t border-gray-100 rounded-b-xl flex justify-between items-center">
          <p className="text-xs text-gray-500 max-w-lg">
             <span className="font-bold text-gray-700">Motivo:</span> {change.justificacion || 'Mejora de fluidez.'}
          </p>
          <div className="flex gap-2">
             {change.status !== 'pending' && (
                <button onClick={onReset} className="text-xs font-bold text-gray-400 hover:text-gray-600 px-3 py-1.5 transition-colors">Deshacer</button>
             )}
             {change.status !== 'rejected' && (
                <button onClick={onReject} className="flex items-center gap-1.5 text-xs font-bold text-red-600 bg-white border border-red-100 hover:bg-red-50 px-3 py-1.5 rounded-lg shadow-sm transition-all"><X className="w-3 h-3" /> Rechazar</button>
             )}
             {change.status !== 'accepted' && (
                <button onClick={onAccept} className="flex items-center gap-1.5 text-xs font-bold text-green-700 bg-green-100 hover:bg-green-200 border border-green-200 px-4 py-1.5 rounded-lg shadow-sm transition-all"><Check className="w-3 h-3" /> Aceptar</button>
             )}
          </div>
       </div>
    </div>
  );
}

function NoteCard({ note }) {
  const severidadColors = {
    alta: 'border-red-200 bg-red-50 text-red-800',
    media: 'border-yellow-200 bg-yellow-50 text-yellow-800',
    baja: 'border-blue-200 bg-blue-50 text-blue-800'
  };
  
  // Normalizar severidad para evitar crashes si viene undefined
  const sev = note.severidad ? note.severidad.toLowerCase() : 'media';
  const theme = severidadColors[sev] || severidadColors.media;

  // Extraer clases para uso condicional
  const bgClass = theme.split(' ')[1];
  const textClass = theme.split(' ')[2];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className={`px-6 py-3 border-b flex justify-between items-center ${bgClass} bg-opacity-50`}>
        <div className="flex items-center gap-3">
          <span className={`text-[10px] font-extrabold uppercase px-2 py-1 rounded-md bg-white/60 ${textClass}`}>
            {note.tipo || 'Nota'}
          </span>
          <span className="text-xs text-gray-500 font-mono">
            {note.parrafo_aprox ? `Párrafo ~${note.parrafo_aprox}` : 'General'}
          </span>
        </div>
        <span className={`text-[10px] font-bold uppercase ${textClass}`}>
          Severidad: {note.severidad || 'Media'}
        </span>
      </div>
      
      <div className="p-6">
        {note.texto_referencia && (
          <div className="mb-4 pl-4 border-l-2 border-gray-300 italic text-gray-500 text-sm font-serif">
            "{note.texto_referencia}..."
          </div>
        )}
        <p className="text-gray-800 font-medium mb-3 leading-relaxed">
          {note.nota}
        </p>
        <div className="bg-blue-50 p-4 rounded-lg text-sm text-blue-900 flex gap-3 items-start mt-4">
          <span className="font-bold text-blue-600 shrink-0 mt-0.5">Sugerencia:</span>
          <p>{note.sugerencia}</p>
        </div>
      </div>
    </div>
  );
}