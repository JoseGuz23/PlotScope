// =============================================================================
// Upload.jsx - SUBIR NUEVO MANUSCRITO
// =============================================================================

import { useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { projectsAPI } from '../services/api';
import {
  Upload as UploadIcon,
  FileText,
  X,
  ChevronLeft,
  Loader2,
  AlertCircle,
  CheckCircle,
  Info,
} from 'lucide-react';

const ACCEPTED_FORMATS = ['.md', '.txt', '.docx'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

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
    
    // Validar formato
    const ext = '.' + f.name.split('.').pop().toLowerCase();
    if (!ACCEPTED_FORMATS.includes(ext)) {
      setError(`Formato no soportado. Usa: ${ACCEPTED_FORMATS.join(', ')}`);
      return;
    }
    
    // Validar tamaño
    if (f.size > MAX_FILE_SIZE) {
      setError('El archivo es muy grande. Máximo: 10MB');
      return;
    }
    
    setFile(f);
    
    // Auto-generar nombre del proyecto si está vacío
    if (!projectName) {
      const name = f.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');
      setProjectName(name);
    }
  }

  function removeFile() {
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    
    if (!file || !projectName.trim()) {
      setError('Selecciona un archivo y dale nombre al proyecto');
      return;
    }

    try {
      setIsUploading(true);
      setError(null);
      
      // TODO: Implementar upload real
      // const result = await projectsAPI.startJob(file, projectName);
      
      // Por ahora simulamos
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      alert('¡Proyecto creado! (Demo - en producción iniciaría el procesamiento)');
      navigate('/');
      
    } catch (err) {
      setError(err.message || 'Error al subir el archivo');
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <>
      {/* Header */}
      <header className="report-divider py-4">
        <Link 
          to="/" 
          className="text-theme-subtle hover:text-theme-primary text-sm mb-2 inline-flex items-center gap-1"
        >
          <ChevronLeft size={16} /> Volver al Dashboard
        </Link>
        <h1 className="text-3xl font-report-serif font-extrabold text-theme-text">
          NUEVO PROYECTO
        </h1>
        <p className="text-sm font-report-mono text-theme-subtle mt-1">
          Sube tu manuscrito para comenzar el análisis y edición
        </p>
      </header>

      <div className="max-w-2xl">
        <form onSubmit={handleSubmit}>
          {/* Nombre del proyecto */}
          <div className="mb-6">
            <label className="block font-bold text-sm mb-2">
              Nombre del Proyecto
            </label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="Ej: Mi Nueva Novela"
              className="w-full px-4 py-3 border border-theme-border rounded-sm text-sm focus:outline-none focus:ring-2 focus:ring-theme-primary/30"
              required
            />
          </div>

          {/* Zona de drop */}
          <div className="mb-6">
            <label className="block font-bold text-sm mb-2">
              Manuscrito
            </label>
            
            {!file ? (
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`
                  border-2 border-dashed rounded-sm p-10 text-center cursor-pointer transition
                  ${isDragging 
                    ? 'border-theme-primary bg-theme-primary/5' 
                    : 'border-theme-border hover:border-theme-primary/50 hover:bg-gray-50'
                  }
                `}
              >
                <UploadIcon 
                  size={48} 
                  className={`mx-auto mb-4 ${isDragging ? 'text-theme-primary' : 'text-gray-400'}`} 
                />
                <p className="text-lg font-bold text-theme-text mb-2">
                  Arrastra tu archivo aquí
                </p>
                <p className="text-sm text-theme-subtle mb-4">
                  o haz clic para seleccionar
                </p>
                <p className="text-xs text-gray-400">
                  Formatos: {ACCEPTED_FORMATS.join(', ')} | Máx: 10MB
                </p>
              </div>
            ) : (
              <div className="border border-theme-border rounded-sm p-4 bg-green-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-green-100 rounded">
                      <FileText className="text-green-600" size={24} />
                    </div>
                    <div>
                      <p className="font-bold text-sm">{file.name}</p>
                      <p className="text-xs text-gray-500">
                        {(file.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={removeFile}
                    className="p-2 hover:bg-green-100 rounded transition"
                  >
                    <X size={20} className="text-gray-500" />
                  </button>
                </div>
              </div>
            )}
            
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED_FORMATS.join(',')}
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>

          {/* Error */}
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-sm flex items-center gap-2">
              <AlertCircle size={18} />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {/* Info sobre el proceso */}
          <div className="mb-6 bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-sm">
            <div className="flex items-start gap-2">
              <Info size={18} className="mt-0.5 flex-shrink-0" />
              <div className="text-sm">
                <p className="font-bold mb-1">¿Qué sucederá?</p>
                <ol className="list-decimal list-inside space-y-1 text-blue-700">
                  <li>Analizaremos tu manuscrito con IA (20-40 min)</li>
                  <li>Generaremos una "Biblia Narrativa" para tu revisión</li>
                  <li>Podrás ajustar el análisis antes de continuar</li>
                  <li>El editor IA aplicará cambios editoriales</li>
                  <li>Revisarás y aprobarás cada cambio</li>
                </ol>
              </div>
            </div>
          </div>

          {/* Botones */}
          <div className="flex gap-4">
            <Link
              to="/"
              className="px-6 py-3 border border-theme-border rounded-sm font-bold text-sm hover:bg-gray-50 transition"
            >
              Cancelar
            </Link>
            <button
              type="submit"
              disabled={!file || !projectName.trim() || isUploading}
              className={`
                flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-sm font-bold text-sm transition
                ${file && projectName.trim() && !isUploading
                  ? 'bg-theme-primary text-white hover:bg-theme-primary/80'
                  : 'bg-gray-200 text-gray-500 cursor-not-allowed'
                }
              `}
            >
              {isUploading ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  Subiendo...
                </>
              ) : (
                <>
                  <CheckCircle size={18} />
                  Crear Proyecto e Iniciar Análisis
                </>
              )}
            </button>
          </div>
        </form>

        {/* Pricing reminder */}
        <div className="mt-8 p-4 border border-theme-border rounded-sm bg-white">
          <p className="text-sm text-center text-theme-subtle">
            <span className="font-bold text-theme-text">$49 USD</span> por libro procesado
            <br />
            <span className="text-xs">Incluye análisis completo + edición + revisión ilimitada</span>
          </p>
        </div>
      </div>
    </>
  );
}
