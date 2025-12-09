// =============================================================================
// Upload.jsx - SUBIDA DE MANUSCRITO + INICIO DE ORQUESTADOR
// =============================================================================

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadAPI } from '../services/api';

export default function Upload() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [projectName, setProjectName] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStage, setUploadStage] = useState(''); // '', 'uploading', 'starting'
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setError('');
      
      // Auto-completar nombre del proyecto
      if (!projectName) {
        const name = selectedFile.name.replace(/\.[^/.]+$/, "");
        setProjectName(name);
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file || !projectName) return;

    setIsUploading(true);
    setError('');
    setUploadStage('uploading');

    try {
      // 1. Subir archivo y crear proyecto
      const uploadResult = await uploadAPI.uploadManuscript(file, projectName);
      
      console.log('Upload result:', uploadResult);
      
      if (!uploadResult.job_id) {
        throw new Error('No se recibió job_id del servidor');
      }
      
      setUploadStage('starting');
      
      // 2. Iniciar el orquestador
      const startResult = await uploadAPI.startOrchestrator(uploadResult.job_id, uploadResult.blob_path);
      
      console.log('Start result:', startResult);
      
      // 3. Redirigir a la página de status
      navigate(`/proyecto/${uploadResult.job_id}/status`);
      
    } catch (err) {
      console.error('❌ Error:', err);
      setError(err.message || 'Error al procesar el archivo. Intenta de nuevo.');
      setIsUploading(false);
      setUploadStage('');
    }
  };

  return (
    <div className="max-w-2xl mx-auto pt-10">
      <div className="text-center mb-12">
        <span className="font-mono text-xs font-bold text-theme-primary uppercase tracking-widest mb-2 block">
          Paso 1 de 3
        </span>
        <h1 className="font-editorial text-4xl font-bold text-gray-900 mb-4">
          Cargar Manuscrito
        </h1>
        <p className="font-sans text-gray-500">
          Sube tu archivo .docx para comenzar la segmentación y análisis.
        </p>
      </div>

      <div className="bg-white border-t-4 border-gray-900 shadow-xl p-10 rounded-sm">
        <form onSubmit={handleSubmit} className="space-y-8">
          
          {/* Título del proyecto */}
          <div>
            <label className="block text-xs font-extrabold uppercase text-gray-500 mb-2 tracking-wide">
              Título de la Obra
            </label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="Ej. La Sombra del Viento"
              className="w-full p-4 border-2 border-gray-200 rounded-sm font-editorial text-xl text-gray-900 focus:border-theme-primary focus:outline-none transition-colors placeholder-gray-300"
              disabled={isUploading}
            />
          </div>

          {/* Selector de archivo */}
          <div>
            <label className="block text-xs font-extrabold uppercase text-gray-500 mb-2 tracking-wide">
              Archivo Fuente (.docx)
            </label>
            <div className={`
              border-2 border-dashed rounded-sm p-12 text-center transition-all cursor-pointer group
              ${file ? 'border-theme-primary bg-green-50' : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'}
              ${isUploading ? 'pointer-events-none opacity-60' : ''}
            `}>
              <input
                type="file"
                accept=".docx"
                onChange={handleFileChange}
                className="hidden"
                id="file-upload"
                disabled={isUploading}
              />
              <label htmlFor="file-upload" className="cursor-pointer block w-full h-full">
                {file ? (
                  <div>
                    <div className="text-4xl mb-3">📄</div>
                    <p className="font-bold text-theme-primary text-lg">{file.name}</p>
                    <p className="font-mono text-xs text-gray-500 mt-2">
                      {(file.size / 1024 / 1024).toFixed(2)} MB • Listo para subir
                    </p>
                  </div>
                ) : (
                  <div>
                    <div className="text-4xl mb-3 text-gray-300 group-hover:text-gray-400 transition-colors">⬇</div>
                    <p className="font-bold text-gray-900">Haz clic para seleccionar</p>
                    <p className="font-sans text-sm text-gray-500 mt-1">Soporta documentos Word estándar</p>
                  </div>
                )}
              </label>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="text-red-700 text-sm font-bold text-center bg-red-50 p-4 border border-red-100 rounded-sm">
              ⚠️ {error}
            </div>
          )}

          {/* Progress indicator */}
          {isUploading && (
            <div className="bg-theme-primary/10 border border-theme-primary/30 rounded-sm p-4">
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 border-2 border-theme-primary border-t-transparent rounded-full animate-spin"></div>
                <div>
                  <p className="font-bold text-theme-primary">
                    {uploadStage === 'uploading' && 'Subiendo archivo...'}
                    {uploadStage === 'starting' && 'Iniciando orquestador...'}
                  </p>
                  <p className="text-xs text-theme-primary/70">
                    {uploadStage === 'uploading' && 'Guardando tu manuscrito en la nube'}
                    {uploadStage === 'starting' && 'Preparando el análisis de tu obra'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Submit button */}
          <div className="pt-6">
            <button
              type="submit"
              disabled={!file || !projectName || isUploading}
              className="w-full bg-theme-primary hover:bg-theme-primary-hover text-white font-extrabold py-4 px-6 rounded-sm shadow-lg transition-all transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed uppercase tracking-widest text-sm"
            >
              {isUploading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  Procesando...
                </span>
              ) : (
                'INICIAR ANÁLISIS'
              )}
            </button>
          </div>

        </form>
      </div>

      {/* Info box */}
      <div className="mt-8 bg-gray-50 border border-gray-200 rounded-sm p-6">
        <h3 className="font-bold text-gray-700 mb-3">¿Qué sucederá?</h3>
        <ol className="text-sm text-gray-600 space-y-2">
          <li className="flex items-start gap-2">
            <span className="font-mono text-theme-primary font-bold">1.</span>
            <span>Tu manuscrito se subirá de forma segura a nuestra nube</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="font-mono text-theme-primary font-bold">2.</span>
            <span>Se dividirá automáticamente en capítulos</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="font-mono text-theme-primary font-bold">3.</span>
            <span>Nuestros modelos de IA analizarán la estructura y estilo</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="font-mono text-theme-primary font-bold">4.</span>
            <span>Generaremos una "Biblia Narrativa" para tu revisión</span>
          </li>
        </ol>
        <p className="text-xs text-gray-400 mt-4">
          ⏱ Tiempo estimado: 5-30 minutos según el tamaño del manuscrito
        </p>
      </div>
    </div>
  );
}