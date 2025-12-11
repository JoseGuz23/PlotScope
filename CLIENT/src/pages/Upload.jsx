// =============================================================================
// Upload.jsx - Subida de Manuscrito (V2 Robustez)
// =============================================================================

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadAPI } from '../services/api';
import { Upload as UploadIcon, FileText, Loader2, AlertCircle } from 'lucide-react';

export default function Upload() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [projectName, setProjectName] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile) => {
    if (!selectedFile.name.endsWith('.docx')) {
      setError('Por favor sube un archivo .docx válido');
      return;
    }
    setFile(selectedFile);
    // Auto-fill nombre si está vacío
    if (!projectName) {
      setProjectName(selectedFile.name.replace('.docx', '').replace(/_/g, ' '));
    }
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file || !projectName) {
      setError('Todos los campos son requeridos');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      // 1. Subir archivo y crear registro
      console.log('Iniciando subida...');
      const uploadRes = await uploadAPI.uploadManuscript(file, projectName);
      
      if (!uploadRes || !uploadRes.job_id) {
        throw new Error('La respuesta del servidor no incluyó un ID de trabajo válido.');
      }
      
      console.log('Subida exitosa, ID:', uploadRes.job_id);

      // 2. Iniciar orquestador explícitamente
      // Nota: El backend v2 devuelve start_url, pero usamos el helper para consistencia
      const startRes = await uploadAPI.startOrchestrator(
        uploadRes.job_id, 
        uploadRes.blob_path,
        projectName // <--- AGREGAR ESTO
      );
      
      console.log('Orquestador iniciado:', startRes);

      // 3. Redirigir a status
      navigate(`/proyecto/${uploadRes.job_id}/status`);

    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message || 'Error al conectar con el servidor');
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto pt-10 px-4">
      <div className="text-center mb-10">
        <span className="font-mono text-xs font-bold text-theme-primary uppercase tracking-widest mb-2 block">
          Paso 1 de 3
        </span>
        <h1 className="font-editorial text-4xl font-bold text-gray-900 mb-4">
          Comencemos el Análisis
        </h1>
        <p className="font-sans text-gray-500">
          Sube tu manuscrito en formato .docx para iniciar el proceso de evaluación editorial.
        </p>
      </div>

      <div className="bg-white border border-gray-200 rounded-sm shadow-xl p-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          
          {/* Project Name Input */}
          <div>
            <label className="block text-sm font-bold text-gray-700 mb-2 uppercase tracking-wide">
              Título de la Obra
            </label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="Ej: El Misterio de la Noche..."
              className="w-full p-3 border border-gray-300 rounded-sm focus:border-theme-primary focus:ring-1 focus:ring-theme-primary outline-none transition-all font-serif"
            />
          </div>

          {/* Drag & Drop Area */}
          <div
            className={`
              relative border-2 border-dashed rounded-sm p-8 text-center transition-all cursor-pointer
              ${dragActive ? 'border-theme-primary bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
              ${file ? 'bg-gray-50' : ''}
            `}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-upload').click()}
          >
            <input
              id="file-upload"
              type="file"
              accept=".docx"
              onChange={handleFileChange}
              className="hidden"
            />

            {file ? (
              <div className="flex flex-col items-center">
                <div className="w-12 h-12 bg-theme-primary text-white rounded-full flex items-center justify-center mb-3 shadow-md">
                  <FileText className="w-6 h-6" />
                </div>
                <p className="font-bold text-gray-900">{file.name}</p>
                <p className="text-xs text-gray-500 mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                <button 
                  type="button"
                  onClick={(e) => { e.stopPropagation(); setFile(null); }}
                  className="mt-4 text-xs text-red-500 hover:text-red-700 font-bold uppercase tracking-wide"
                >
                  Eliminar archivo
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center py-4">
                <UploadIcon className="w-10 h-10 text-gray-400 mb-3" />
                <p className="text-gray-900 font-medium mb-1">
                  Arrastra tu archivo aquí
                </p>
                <p className="text-sm text-gray-500 mb-4">o haz clic para buscar</p>
                <span className="text-[10px] uppercase tracking-widest text-gray-400 border border-gray-200 px-2 py-1 rounded">
                  Solo formato .DOCX
                </span>
              </div>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
              <p className="text-sm text-red-700 font-medium">{error}</p>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={!file || !projectName || isUploading}
            className={`
              w-full py-4 px-6 rounded-sm text-white font-bold uppercase tracking-widest transition-all
              flex items-center justify-center gap-3 shadow-lg
              ${!file || !projectName || isUploading 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-theme-primary hover:bg-theme-primary-hover transform hover:-translate-y-0.5'}
            `}
          >
            {isUploading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Procesando...</span>
              </>
            ) : (
              <>
                <span>Subir y Analizar</span>
                <span className="text-lg">→</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}