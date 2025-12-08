// =============================================================================
// Editor.jsx - EDITOR CON TRACK CHANGES (PLACEHOLDER)
// =============================================================================
// Por ahora muestra el manuscrito anotado. TipTap vendrá en la siguiente fase.
// =============================================================================

import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { manuscriptAPI } from '../services/api';
import {
  FileText,
  Download,
  ChevronLeft,
  ChevronRight,
  Check,
  X,
  Loader2,
  Eye,
  Code,
  Filter,
} from 'lucide-react';

export default function Editor() {
  const { id: projectId } = useParams();
  
  const [content, setContent] = useState('');
  const [annotatedContent, setAnnotatedContent] = useState('');
  const [changesHTML, setChangesHTML] = useState('');
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('annotated'); // 'clean' | 'annotated' | 'html'

  useEffect(() => {
    loadContent();
  }, [projectId]);

  async function loadContent() {
    try {
      setIsLoading(true);
      
      const [edited, annotated, html, summaryData] = await Promise.all([
        manuscriptAPI.getEdited(projectId).catch(() => ''),
        manuscriptAPI.getAnnotated(projectId).catch(() => ''),
        manuscriptAPI.getChangesHTML(projectId).catch(() => ''),
        manuscriptAPI.getSummary(projectId).catch(() => null),
      ]);
      
      setContent(edited);
      setAnnotatedContent(annotated);
      setChangesHTML(html);
      setSummary(summaryData);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="animate-spin text-theme-primary" size={40} />
        <span className="ml-3 text-theme-subtle">Cargando editor...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-sm">
        <p className="font-bold">Error al cargar el manuscrito</p>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <>
      {/* Header */}
      <header className="report-divider py-4">
        <div className="flex justify-between items-center">
          <div>
            <Link 
              to="/" 
              className="text-theme-subtle hover:text-theme-primary text-sm mb-2 inline-flex items-center gap-1"
            >
              <ChevronLeft size={16} /> Volver al Dashboard
            </Link>
            <h1 className="text-3xl font-report-serif font-extrabold text-theme-text">
              EDITOR DE MANUSCRITO
            </h1>
            {summary && (
              <p className="text-sm font-report-mono text-theme-subtle mt-1">
                {summary.book_name} | {summary.estadisticas?.total_words?.toLocaleString()} palabras | {summary.estadisticas?.total_changes} cambios
              </p>
            )}
          </div>
          <div className="flex gap-3">
            <a
              href={summary?.urls?.manuscrito_limpio}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 border border-theme-border rounded-sm text-sm font-bold hover:bg-gray-50 transition"
            >
              <Download size={18} />
              Descargar Limpio
            </a>
            <a
              href={summary?.urls?.manuscrito_anotado}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 bg-theme-primary text-white px-4 py-2 rounded-sm text-sm font-bold hover:bg-theme-primary/80 transition"
            >
              <Download size={18} />
              Descargar Anotado
            </a>
          </div>
        </div>
      </header>

      {/* Stats rápidos */}
      {summary && (
        <div className="grid grid-cols-5 gap-4 mb-6">
          <div className="border border-theme-border bg-white p-4 rounded-sm">
            <p className="data-label">Capítulos</p>
            <p className="text-2xl font-report-mono font-bold">{summary.capitulos_procesados}</p>
          </div>
          <div className="border border-theme-border bg-white p-4 rounded-sm">
            <p className="data-label">Cambios</p>
            <p className="text-2xl font-report-mono font-bold text-theme-primary">
              {summary.estadisticas?.total_changes}
            </p>
          </div>
          <div className="border border-theme-border bg-white p-4 rounded-sm">
            <p className="data-label">Costo</p>
            <p className="text-2xl font-report-mono font-bold text-green-600">
              ${summary.estadisticas?.total_cost_usd?.toFixed(2)}
            </p>
          </div>
          <div className="border border-theme-border bg-white p-4 rounded-sm">
            <p className="data-label">Tiempo Total</p>
            <p className="text-lg font-report-mono font-bold">
              {summary.tiempos?.total?.split('.')[0] || '—'}
            </p>
          </div>
          <div className="border border-theme-border bg-white p-4 rounded-sm">
            <p className="data-label">Versión</p>
            <p className="text-lg font-report-mono font-bold">{summary.version}</p>
          </div>
        </div>
      )}

      {/* Selector de vista */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setViewMode('annotated')}
          className={`flex items-center gap-2 px-4 py-2 rounded-sm text-sm font-bold transition ${
            viewMode === 'annotated' 
              ? 'bg-theme-primary text-white' 
              : 'bg-white border border-theme-border hover:bg-gray-50'
          }`}
        >
          <Eye size={18} />
          Vista Anotada
        </button>
        <button
          onClick={() => setViewMode('clean')}
          className={`flex items-center gap-2 px-4 py-2 rounded-sm text-sm font-bold transition ${
            viewMode === 'clean' 
              ? 'bg-theme-primary text-white' 
              : 'bg-white border border-theme-border hover:bg-gray-50'
          }`}
        >
          <FileText size={18} />
          Vista Limpia
        </button>
        <button
          onClick={() => setViewMode('html')}
          className={`flex items-center gap-2 px-4 py-2 rounded-sm text-sm font-bold transition ${
            viewMode === 'html' 
              ? 'bg-theme-primary text-white' 
              : 'bg-white border border-theme-border hover:bg-gray-50'
          }`}
        >
          <Code size={18} />
          Control de Cambios
        </button>
      </div>

      {/* Área del editor */}
      <div className="border border-theme-border bg-white rounded-sm min-h-[600px]">
        {/* Toolbar placeholder */}
        <div className="border-b border-theme-border p-3 bg-gray-50 flex justify-between items-center">
          <div className="flex gap-2">
            <button className="p-2 hover:bg-gray-200 rounded transition" title="Cambio anterior">
              <ChevronLeft size={18} />
            </button>
            <button className="p-2 hover:bg-gray-200 rounded transition" title="Cambio siguiente">
              <ChevronRight size={18} />
            </button>
            <span className="text-sm text-theme-subtle self-center px-2">
              Navegación de cambios (próximamente)
            </span>
          </div>
          <div className="flex gap-2">
            <button className="flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded text-sm font-bold hover:bg-green-200 transition">
              <Check size={16} /> Aceptar Todo
            </button>
            <button className="flex items-center gap-1 px-3 py-1 bg-red-100 text-red-700 rounded text-sm font-bold hover:bg-red-200 transition">
              <X size={16} /> Rechazar Todo
            </button>
          </div>
        </div>

        {/* Contenido */}
        <div className="p-6 max-h-[700px] overflow-y-auto">
          {viewMode === 'html' ? (
            <div 
              className="prose prose-sm max-w-none"
              dangerouslySetInnerHTML={{ __html: changesHTML }}
            />
          ) : (
            <pre className="whitespace-pre-wrap font-report-mono text-sm leading-relaxed">
              {viewMode === 'annotated' ? annotatedContent : content}
            </pre>
          )}
        </div>
      </div>

      {/* Nota sobre TipTap */}
      <div className="mt-6 bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-sm">
        <p className="font-bold text-sm">🚧 Editor Interactivo en Desarrollo</p>
        <p className="text-sm mt-1">
          La siguiente versión incluirá el editor TipTap con track changes interactivo: 
          aceptar/rechazar cambios individuales, navegación entre cambios, y export final.
        </p>
      </div>

      {/* Links a archivos */}
      {summary?.urls && (
        <div className="mt-6 border border-theme-border bg-white p-4 rounded-sm">
          <h3 className="font-bold text-sm mb-3">📎 Archivos Generados</h3>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(summary.urls).map(([key, url]) => (
              <a
                key={key}
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-theme-primary hover:underline flex items-center gap-2"
              >
                <FileText size={14} />
                {key.replace(/_/g, ' ')}
              </a>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
