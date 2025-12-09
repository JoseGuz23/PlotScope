// =============================================================================
// Editor.jsx - VISOR DE MANUSCRITO (Versión Robusta)
// =============================================================================

import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { manuscriptAPI } from '../services/api';
import { 
  FileText, Download, ArrowLeft, Loader2, 
  BookOpen, AlignLeft, Type
} from 'lucide-react';

export default function Editor() {
  const { id: projectId } = useParams();
  
  const [content, setContent] = useState('');
  const [chapters, setChapters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeChapter, setActiveChapter] = useState(0);

  useEffect(() => {
    loadManuscript();
  }, [projectId]);

  async function loadManuscript() {
    try {
      const text = await manuscriptAPI.getEdited(projectId);
      setContent(text);
      
      // REGEX MEJORADO: Detecta # Header, ## Header, o patrones "Capítulo X"
      // Separa el texto en bloques lógicos
      const regex = /(^#{1,2}\s+.*$|^Capítulo\s+\d+.*$|^Prólogo.*$)/gm;
      
      let parts = text.split(regex).filter(p => p.trim().length > 0);
      let detectedChapters = [];
      
      // Reconstruir estructura (Titulo + Contenido)
      for (let i = 0; i < parts.length; i++) {
        const line = parts[i].trim();
        // Si parece un título y el siguiente bloque es texto largo...
        if ((line.startsWith('#') || line.toLowerCase().startsWith('capítulo') || line.toLowerCase().startsWith('prólogo')) && parts[i+1]) {
           detectedChapters.push({
             title: line.replace(/[#*]/g, '').trim(),
             content: parts[i+1]
           });
           i++; // Saltar el contenido ya usado
        }
      }

      // Fallback si no detecta nada (todo es un capitulo)
      if (detectedChapters.length === 0) {
        detectedChapters = [{ title: 'Manuscrito Completo', content: text }];
      }

      setChapters(detectedChapters);
      
    } catch (err) {
      console.error(err);
      alert("No se pudo cargar el manuscrito. ¿Ya finalizó el proceso?");
    } finally {
      setLoading(false);
    }
  }

  const handleExport = async () => {
    try {
      const blob = await manuscriptAPI.export(projectId);
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Manuscrito_${projectId}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert("Error exportando: " + err.message);
    }
  };

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-50">
      <Loader2 className="w-10 h-10 animate-spin text-theme-primary mb-4" />
      <p className="text-gray-500 font-mono text-xs uppercase tracking-widest">Cargando Manuscrito...</p>
    </div>
  );

  return (
    <div className="flex h-screen bg-[#f8f9fa] font-sans overflow-hidden">
      
      {/* SIDEBAR */}
      <aside className="w-72 bg-white border-r border-gray-200 flex flex-col shrink-0 z-20">
        <div className="p-5 border-b border-gray-100">
          <h2 className="font-bold text-gray-800 flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-theme-primary" /> Índice
          </h2>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-1 custom-scrollbar">
          {chapters.map((chap, idx) => (
            <button
              key={idx}
              onClick={() => setActiveChapter(idx)}
              className={`w-full text-left px-4 py-3 rounded-lg text-sm transition-all truncate ${activeChapter === idx ? 'bg-gray-900 text-white font-medium shadow-md' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'}`}
            >
              {chap.title}
            </button>
          ))}
        </div>
        <div className="p-4 border-t border-gray-100">
           <Link to="/dashboard" className="text-xs font-bold text-gray-400 hover:text-gray-700 flex items-center gap-2 justify-center">
             <ArrowLeft className="w-3 h-3" /> VOLVER AL DASHBOARD
           </Link>
        </div>
      </aside>

      {/* ÁREA PRINCIPAL */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 bg-white border-b border-gray-200 flex justify-between items-center px-8 shrink-0 shadow-sm">
           <div className="flex items-center gap-4 text-gray-400">
              <span className="text-xs font-bold uppercase tracking-widest text-gray-300">Modo Lectura</span>
           </div>
           <button onClick={handleExport} className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-md text-xs font-bold uppercase tracking-wider hover:bg-black transition-all">
             <Download className="w-3 h-3" /> Exportar
           </button>
        </header>

        <div className="flex-1 overflow-y-auto bg-[#f8f9fa] p-8 lg:p-12 flex justify-center custom-scrollbar">
           <div className="w-full max-w-3xl bg-white shadow-sm border border-gray-200 min-h-[800px] p-12 lg:p-16 rounded-sm">
              <h1 className="font-editorial text-4xl mb-8 text-gray-900">{chapters[activeChapter]?.title}</h1>
              <div className="prose prose-lg prose-slate max-w-none font-serif leading-relaxed text-gray-700 whitespace-pre-wrap">
                 {chapters[activeChapter]?.content}
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}