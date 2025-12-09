// =============================================================================
// Editor.jsx - LECTOR Y EDITOR DE MANUSCRITO FINAL
// =============================================================================

import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { manuscriptAPI } from '../services/api';
import { 
  FileText, Download, Save, ArrowLeft, Loader2, 
  BookOpen, AlignLeft, Type
} from 'lucide-react';

export default function Editor() {
  const { id: projectId } = useParams();
  
  const [content, setContent] = useState('');
  const [chapters, setChapters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeChapter, setActiveChapter] = useState(0);

  useEffect(() => {
    loadManuscript();
  }, [projectId]);

  async function loadManuscript() {
    try {
      // Carga el texto completo editado
      const text = await manuscriptAPI.getEdited(projectId);
      setContent(text);
      
      // Intentar extraer capítulos (simulado por ahora basado en headers Markdown)
      const chaps = text.split(/^# /m).filter(Boolean).map((c, i) => ({
        id: i,
        title: c.split('\n')[0].substring(0, 30) + '...',
        content: '# ' + c
      }));
      setChapters(chaps.length > 0 ? chaps : [{id: 0, title: 'Manuscrito Completo', content: text}]);
      
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  const handleExport = async () => {
    try {
      const blob = await manuscriptAPI.export(projectId);
      // Crear link de descarga
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Manuscrito_${projectId}.docx`); // O .json según lo que mande el back
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert("Error exportando: " + err.message);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-screen bg-white">
      <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
    </div>
  );

  return (
    <div className="flex h-screen bg-[#f8f9fa] font-sans">
      
      {/* SIDEBAR CAPÍTULOS */}
      <aside className="w-72 bg-white border-r border-gray-200 flex flex-col shrink-0 z-20">
        <div className="p-5 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-bold text-gray-800 flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-theme-primary" /> Capítulos
          </h2>
        </div>
        
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {chapters.map((chap, idx) => (
            <button
              key={idx}
              onClick={() => setActiveChapter(idx)}
              className={`
                w-full text-left px-4 py-3 rounded-lg text-sm transition-all
                ${activeChapter === idx 
                  ? 'bg-gray-900 text-white font-medium shadow-md' 
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'}
              `}
            >
              <span className="opacity-50 text-xs mr-2">{(idx + 1).toString().padStart(2, '0')}</span>
              {chap.title.replace(/[#*]/g, '')}
            </button>
          ))}
        </div>

        <div className="p-4 border-t border-gray-100">
           <Link to="/dashboard" className="text-xs font-bold text-gray-400 hover:text-gray-700 flex items-center gap-1">
             <ArrowLeft className="w-3 h-3" /> VOLVER AL DASHBOARD
           </Link>
        </div>
      </aside>

      {/* ÁREA PRINCIPAL */}
      <div className="flex-1 flex flex-col min-w-0">
        
        {/* Toolbar Flotante */}
        <header className="h-16 bg-white border-b border-gray-200 flex justify-between items-center px-8 shrink-0">
           <div className="flex items-center gap-4 text-gray-400">
              <Type className="w-4 h-4 hover:text-gray-800 cursor-pointer transition-colors" />
              <div className="h-4 w-[1px] bg-gray-200"></div>
              <AlignLeft className="w-4 h-4 hover:text-gray-800 cursor-pointer transition-colors" />
           </div>

           <div className="flex gap-3">
              <button 
                onClick={handleExport}
                className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-md text-xs font-bold uppercase tracking-wider hover:bg-black transition-all"
              >
                <Download className="w-3 h-3" /> Exportar
              </button>
           </div>
        </header>

        {/* Editor / Visor */}
        <div className="flex-1 overflow-y-auto bg-[#f8f9fa] p-8 lg:p-12 flex justify-center">
           <div className="w-full max-w-3xl bg-white shadow-sm border border-gray-200 min-h-[800px] p-12 lg:p-16 rounded-sm">
              <div className="prose prose-lg prose-slate max-w-none font-serif leading-relaxed">
                 {/* Renderizado simple del contenido markdown/texto */}
                 {chapters[activeChapter]?.content.split('\n').map((line, i) => (
                    <p key={i} className="mb-4 text-gray-800">
                      {line.replace(/^#+ /, '')} {/* Limpieza visual simple */}
                    </p>
                 ))}
              </div>
           </div>
        </div>

      </div>
    </div>
  );
}