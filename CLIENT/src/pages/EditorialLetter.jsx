// =============================================================================
// EditorialLetter.jsx - V5.1 (Fix de Estructura JSON)
// =============================================================================

import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { editorialAPI } from '../services/api';
import { 
  FileText, Download, Loader2, AlertCircle, 
  ArrowRight, Quote
} from 'lucide-react';
import { saveAs } from 'file-saver';

// --- RENDERIZADOR MARKDOWN (Sin cambios, funciona bien) ---
const SimpleMarkdownRenderer = ({ content }) => {
  if (!content) return null;

  // Normalizamos saltos de línea para asegurar que detecte párrafos
  const normalizedContent = content.replace(/\\n/g, '\n');
  const paragraphs = normalizedContent.split(/\n\n+/);

  return (
    <div className="space-y-6 font-serif text-gray-800 leading-relaxed text-lg">
      {paragraphs.map((bloque, index) => {
        const trimmed = bloque.trim();
        if (!trimmed) return null;
        
        // Títulos
        if (trimmed.startsWith('# ')) return <h1 key={index} className="font-editorial text-4xl text-gray-900 mt-10 mb-6">{trimmed.replace('# ', '')}</h1>;
        if (trimmed.startsWith('## ')) return <h2 key={index} className="font-editorial text-2xl text-theme-primary mt-8 mb-4 border-b border-gray-200 pb-2">{trimmed.replace('## ', '')}</h2>;
        if (trimmed.startsWith('### ')) return <h3 key={index} className="font-bold text-xl text-gray-900 mt-6 mb-2">{trimmed.replace('### ', '')}</h3>;

        // Listas
        if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
            const items = trimmed.split('\n').map(line => line.replace(/^[-*] /, ''));
            return (
                <ul key={index} className="list-disc pl-6 space-y-2 mb-4">
                    {items.map((item, i) => <li key={i} className="text-gray-700">{parseInlineStyles(item)}</li>)}
                </ul>
            );
        }

        // Párrafos normales
        return <p key={index}>{parseInlineStyles(trimmed)}</p>;
      })}
    </div>
  );
};

const parseInlineStyles = (text) => {
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
            return <strong key={i} className="font-bold text-gray-900">{part.slice(2, -2)}</strong>;
        }
        return part;
    });
};

export default function EditorialLetter() {
  const { id: projectId } = useParams();
  const [letterData, setLetterData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLetter();
  }, [projectId]);

  async function loadLetter() {
    try {
      const data = await editorialAPI.getLetter(projectId);
      console.log("📥 DATA RECIBIDA EN FRONTEND:", data); // Mira la consola para verificar
      setLetterData(data);
    } catch (err) {
      console.error("Error cargando carta:", err);
    } finally {
      setLoading(false);
    }
  }

  // --- FUNCIÓN DE EXTRACCIÓN ROBUSTA ---
  // Busca el texto en cualquier lugar donde el backend haya decidido ponerlo
  const getLetterContent = (data) => {
    if (!data) return null;
    
    // 1. Caso directo (Tu caso actual según la consola)
    if (data.texto_completo) return data.texto_completo;
    
    // 2. Caso anidado estándar
    if (data.carta_editorial?.texto_completo) return data.carta_editorial.texto_completo;
    
    // 3. Caso Markdown directo
    if (data.carta_markdown) return data.carta_markdown;
    
    // 4. Caso respuesta con clave 'carta'
    if (data.carta) return data.carta;

    return null;
  };

  const content = getLetterContent(letterData);

  const downloadLetter = () => {
    if (content) {
      const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
      saveAs(blob, `Carta_Editorial_${projectId}.md`);
    }
  };

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-screen bg-[#f8f9fa]">
      <Loader2 className="w-10 h-10 animate-spin text-theme-primary mb-4" />
      <p className="text-gray-500 font-mono text-xs uppercase tracking-widest">Generando Carta Editorial...</p>
    </div>
  );

  // Si después de intentar extraer no hay texto, mostramos pendiente
  if (!content) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-red-50 text-center px-4">
        <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
        <h2 className="text-xl font-bold text-gray-900">Carta Editorial Pendiente</h2>
        <p className="text-gray-600 mb-6 max-w-md mt-2">
           No se encontró el contenido de la carta. Verifica la consola para ver qué estructura devolvió el backend.
        </p>
        <Link to={`/proyecto/${projectId}/status`} className="text-theme-primary font-bold hover:underline border border-theme-primary px-6 py-2 rounded-lg">
          Ver Estado de Procesamiento
        </Link>
        {/* Debug visual para que veas qué llegó si falla */}
        <pre className="mt-8 text-xs text-left bg-gray-100 p-4 rounded overflow-auto max-w-lg max-h-32 text-gray-500">
           Debug: {JSON.stringify(letterData, null, 2)}
        </pre>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-[#f8f9fa] font-sans overflow-hidden">
        {/* SIDEBAR */}
        <aside className="w-72 bg-white border-r border-gray-200 flex flex-col shrink-0 z-20 hidden md:flex">
            <div className="p-6 border-b border-gray-100">
                <h1 className="font-editorial text-2xl font-bold text-gray-900">Carta Editorial</h1>
                <p className="text-xs text-gray-400 mt-1 uppercase tracking-wider">Developmental Edit</p>
            </div>
            <div className="p-6">
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 mb-6">
                    <Quote className="w-5 h-5 text-theme-primary mb-2 opacity-50" />
                    <p className="text-sm text-blue-900 leading-relaxed italic">
                        Esta carta ha sido redactada por la IA para simular un editor humano. Léela con atención antes de pasar a la edición línea por línea.
                    </p>
                </div>
            </div>
            <div className="mt-auto p-6 border-t border-gray-100 bg-gray-50/50">
                <Link 
                    to={`/proyecto/${projectId}/editor`}
                    className="flex items-center justify-center gap-2 w-full py-3 bg-theme-primary text-white rounded-lg font-bold text-sm shadow-lg hover:bg-theme-primary-hover transition-all transform hover:-translate-y-0.5"
                >
                    Ir al Editor <ArrowRight className="w-4 h-4" />
                </Link>
            </div>
        </aside>

        {/* CONTENIDO PRINCIPAL */}
        <main className="flex-1 overflow-y-auto p-4 md:p-12 custom-scrollbar bg-[#f8f9fa]">
            <div className="max-w-4xl mx-auto">
                <div className="flex justify-between items-center mb-8">
                    <div className="flex items-center gap-2 text-gray-400 text-sm font-mono uppercase">
                        <FileText className="w-4 h-4" /> VISTA DE LECTURA
                    </div>
                    <button onClick={downloadLetter} className="flex items-center gap-2 text-gray-700 hover:text-gray-900 text-sm font-bold transition-colors border border-gray-300 bg-white px-4 py-2 rounded-lg shadow-sm hover:shadow">
                        <Download className="w-4 h-4" /> Descargar (.md)
                    </button>
                </div>

                <div className="bg-white p-8 md:p-12 rounded-xl shadow-sm border border-gray-200 min-h-[600px]">
                    <SimpleMarkdownRenderer content={content} />
                </div>
                
                <div className="h-20"></div>
            </div>
        </main>
    </div>
  );
}